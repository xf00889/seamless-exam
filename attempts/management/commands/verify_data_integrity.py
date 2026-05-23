"""
Management command to verify data integrity and persistence.
Can be run after server restarts to ensure data is intact.
"""
from django.core.management.base import BaseCommand
from services.data_integrity_service import DataIntegrityService


class Command(BaseCommand):
    """
    Verify data integrity and persistence across server restarts.
    """
    help = 'Verify data integrity and persistence'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up orphaned data',
        )
    
    def handle(self, *args, **options):
        """Execute the command."""
        service = DataIntegrityService()
        
        self.stdout.write(self.style.SUCCESS('Verifying data persistence...'))
        
        # Verify data persistence
        results = service.verify_data_persistence()
        
        if results.get('database_connected'):
            self.stdout.write(self.style.SUCCESS('✓ Database connected'))
            self.stdout.write(f"  Total attempts: {results['total_attempts']}")
            self.stdout.write(f"  Total answers: {results['total_answers']}")
            self.stdout.write(f"  In-progress attempts: {results['in_progress_attempts']}")
            self.stdout.write(f"  Orphaned answers: {results['orphaned_answers']}")
            
            if results['data_integrity_ok']:
                self.stdout.write(self.style.SUCCESS('✓ Data integrity OK'))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠ Found {results['orphaned_answers']} orphaned answers"
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"✗ Database connection failed: {results.get('error', 'Unknown error')}"
                )
            )
            return
        
        # Cleanup if requested
        if options['cleanup']:
            self.stdout.write(self.style.SUCCESS('\nCleaning up orphaned data...'))
            cleanup_results = service.cleanup_orphaned_data()
            
            if 'error' in cleanup_results:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Cleanup failed: {cleanup_results['error']}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Deleted {cleanup_results['orphaned_answers_deleted']} orphaned answers"
                    )
                )
        
        self.stdout.write(self.style.SUCCESS('\nData integrity verification complete'))
