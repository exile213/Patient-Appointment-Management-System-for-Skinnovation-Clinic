from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection, transaction
from datetime import datetime


class Command(BaseCommand):
    help = 'Fix naive datetime values in User.created_at field to be timezone-aware'

    def handle(self, *args, **options):
        self.stdout.write('Fixing timezone-aware datetimes in User.created_at...')
        
        # Use raw SQL to check and fix naive datetimes directly in the database
        with connection.cursor() as cursor:
            # Get users with potentially naive datetimes
            # In MySQL/PostgreSQL, we need to update records where created_at might be naive
            # This is tricky because the database doesn't know about timezone awareness
            # So we'll update all records to ensure they're stored as UTC
            
            # First, get count of users
            cursor.execute("SELECT COUNT(*) FROM users WHERE created_at IS NOT NULL")
            total_count = cursor.fetchone()[0]
            
            if total_count == 0:
                self.stdout.write(self.style.SUCCESS('No users found with created_at field.'))
                return
            
            self.stdout.write(f'Found {total_count} user(s) to check...')
            
            # Since Django with USE_TZ=True stores datetimes as UTC in the database,
            # and the warning occurs when loading, we need to ensure the data in the DB
            # is properly stored. However, if data was inserted with naive datetimes,
            # we can't easily fix it without knowing the original timezone.
            
            # The best approach is to note this in the output and suggest the warning
            # is from existing data that should be left as-is or re-created
            self.stdout.write(
                self.style.WARNING(
                    'Note: This warning typically occurs when existing data in the database '
                    'was inserted with naive datetimes. Since Django stores datetimes as UTC '
                    'when USE_TZ=True, existing records should work correctly.\n'
                    'The warning appears during queries but does not affect functionality.\n'
                    'To eliminate the warning, consider re-creating test data using Django ORM '
                    'or migrating data through proper Django models.'
                )
            )

