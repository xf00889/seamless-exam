import os
import json
import subprocess
import tempfile
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

SCOPES = ['https://www.googleapis.com/auth/drive.file']


class Command(BaseCommand):
    help = 'Backup database and upload to Google Drive'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep',
            type=int,
            default=7,
            help='Number of backups to retain in Google Drive (default: 7)',
        )
        parser.add_argument(
            '--auth',
            action='store_true',
            help='Run the OAuth2 authorization flow to generate a refresh token',
        )

    def handle(self, *args, **options):
        if not HAS_GOOGLE:
            self.stderr.write(self.style.ERROR(
                'Required packages missing. Install with:\n'
                'pip install google-api-python-client google-auth google-auth-oauthlib'
            ))
            return

        if options['auth']:
            self._run_auth_flow()
            return

        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not folder_id:
            self.stderr.write(self.style.ERROR(
                'GOOGLE_DRIVE_FOLDER_ID environment variable is not set.'
            ))
            return

        creds = self._get_credentials()
        if not creds:
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

            self._upload_to_drive(filepath, filename, creds, folder_id)
            self._cleanup_old_backups(creds, folder_id, options['keep'])

        self.stdout.write(self.style.SUCCESS('Backup completed successfully'))

    def _get_credentials(self):
        refresh_token = os.environ.get('GOOGLE_DRIVE_REFRESH_TOKEN')
        client_id = os.environ.get('GOOGLE_DRIVE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_DRIVE_CLIENT_SECRET')

        if not all([refresh_token, client_id, client_secret]):
            self.stderr.write(self.style.ERROR(
                'Missing OAuth2 credentials. Set these environment variables:\n'
                '  GOOGLE_DRIVE_CLIENT_ID\n'
                '  GOOGLE_DRIVE_CLIENT_SECRET\n'
                '  GOOGLE_DRIVE_REFRESH_TOKEN\n\n'
                'To get the refresh token, run locally:\n'
                '  python manage.py backup_to_drive --auth'
            ))
            return None

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        creds.refresh(Request())
        return creds

    def _run_auth_flow(self):
        client_id = os.environ.get('GOOGLE_DRIVE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_DRIVE_CLIENT_SECRET')

        if not client_id or not client_secret:
            self.stderr.write(self.style.ERROR(
                'Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET first.\n\n'
                'To get these:\n'
                '1. Go to Google Cloud Console > APIs & Services > Credentials\n'
                '2. Create an OAuth 2.0 Client ID (Desktop app type)\n'
                '3. Copy the Client ID and Client Secret'
            ))
            return

        client_config = {
            'installed': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': ['http://localhost'],
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(port=8090)

        self.stdout.write(self.style.SUCCESS('\nAuthorization successful!\n'))
        self.stdout.write('Set this environment variable on your server:\n')
        self.stdout.write(self.style.WARNING(
            f'GOOGLE_DRIVE_REFRESH_TOKEN={creds.refresh_token}'
        ))
        self.stdout.write('\nThis token does not expire unless you revoke it.')

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

    def _upload_to_drive(self, filepath, filename, creds, folder_id):
        service = build('drive', 'v3', credentials=creds)

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

    def _cleanup_old_backups(self, creds, folder_id, keep):
        service = build('drive', 'v3', credentials=creds)

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
