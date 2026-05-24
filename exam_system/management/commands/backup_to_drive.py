import os
import subprocess
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False


class Command(BaseCommand):
    help = 'Backup database and upload to Google Drive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=7,
            help='Number of backups to retain in Google Drive (default: 7)',
        )

    def handle(self, *args, **options):
        if not HAS_GOOGLE:
            self.stderr.write(self.style.ERROR(
                'google-api-python-client and google-auth are required. '
                'Install with: pip install google-api-python-client google-auth'
            ))
            return

        credentials_json = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

        if not credentials_json:
            self.stderr.write(self.style.ERROR(
                'GOOGLE_DRIVE_CREDENTIALS environment variable is not set. '
                'Set it to the path of your service account JSON file or the JSON content itself.'
            ))
            return

        if not folder_id:
            self.stderr.write(self.style.ERROR(
                'GOOGLE_DRIVE_FOLDER_ID environment variable is not set. '
                'Set it to the ID of the Google Drive folder for backups.'
            ))
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_settings = settings.DATABASES['default']
        engine = db_settings.get('ENGINE', '')

        with tempfile.TemporaryDirectory() as tmp_dir:
            if 'mysql' in engine:
                filename = f'backup_{timestamp}.sql'
                filepath = os.path.join(tmp_dir, filename)
                self._dump_mysql(db_settings, filepath)
            elif 'postgresql' in engine or 'postgis' in engine:
                filename = f'backup_{timestamp}.sql'
                filepath = os.path.join(tmp_dir, filename)
                self._dump_postgres(db_settings, filepath)
            elif 'sqlite' in engine:
                filename = f'backup_{timestamp}.sqlite3'
                filepath = os.path.join(tmp_dir, filename)
                self._dump_sqlite(db_settings, filepath)
            else:
                self.stderr.write(self.style.ERROR(f'Unsupported database engine: {engine}'))
                return

            file_size = os.path.getsize(filepath)
            self.stdout.write(f'Database dump created: {filename} ({file_size / 1024:.1f} KB)')

            self._upload_to_drive(filepath, filename, credentials_json, folder_id)
            self._cleanup_old_backups(credentials_json, folder_id, options['keep'])

        self.stdout.write(self.style.SUCCESS('Backup completed successfully'))

    def _dump_mysql(self, db_settings, filepath):
        cmd = [
            'mysqldump',
            f'--host={db_settings["HOST"]}',
            f'--port={db_settings.get("PORT", "3306")}',
            f'--user={db_settings["USER"]}',
            f'--password={db_settings["PASSWORD"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            db_settings['NAME'],
        ]
        with open(filepath, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise Exception(f'mysqldump failed: {result.stderr}')

    def _dump_postgres(self, db_settings, filepath):
        env = os.environ.copy()
        env['PGPASSWORD'] = db_settings.get('PASSWORD', '')

        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            cmd = ['pg_dump', '--no-owner', '--no-acl', database_url]
        else:
            cmd = [
                'pg_dump',
                f'--host={db_settings["HOST"]}',
                f'--port={db_settings.get("PORT", "5432")}',
                f'--username={db_settings["USER"]}',
                '--no-owner',
                '--no-acl',
                db_settings['NAME'],
            ]

        with open(filepath, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, env=env)
        if result.returncode != 0:
            raise Exception(f'pg_dump failed: {result.stderr}')

    def _dump_sqlite(self, db_settings, filepath):
        import shutil
        shutil.copy2(db_settings['NAME'], filepath)

    def _get_drive_service(self, credentials_json):
        if os.path.isfile(credentials_json):
            creds = service_account.Credentials.from_service_account_file(
                credentials_json,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
        else:
            import json
            info = json.loads(credentials_json)
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
        return build('drive', 'v3', credentials=creds)

    def _upload_to_drive(self, filepath, filename, credentials_json, folder_id):
        service = self._get_drive_service(credentials_json)

        file_metadata = {
            'name': filename,
            'parents': [folder_id],
        }
        media = MediaFileUpload(filepath, mimetype='application/sql', resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name'
        ).execute()

        self.stdout.write(f'Uploaded to Google Drive: {file["name"]} (ID: {file["id"]})')

    def _cleanup_old_backups(self, credentials_json, folder_id, keep):
        service = self._get_drive_service(credentials_json)

        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false and name contains 'backup_'",
            orderBy='createdTime desc',
            fields='files(id,name,createdTime)',
            pageSize=100,
        ).execute()

        files = results.get('files', [])
        if len(files) > keep:
            for old_file in files[keep:]:
                service.files().delete(fileId=old_file['id']).execute()
                self.stdout.write(f'Deleted old backup: {old_file["name"]}')
