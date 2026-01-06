from django.core.management.base import BaseCommand
from accounts.models import User, AttendantProfile
from datetime import time


class Command(BaseCommand):
    help = 'Set up work schedules for attendants (Jillian and other attendant)'

    def handle(self, *args, **options):
        # Work schedule: Monday to Saturday, 10:00 AM to 6:00 PM
        work_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        start_time = time(10, 0)  # 10:00 AM
        end_time = time(18, 0)  # 6:00 PM
        
        # Find attendants by name (Jillian and others)
        attendants = User.objects.filter(user_type='attendant')
        
        if not attendants.exists():
            self.stdout.write(self.style.WARNING('No attendants found. Please create attendant users first.'))
            return
        
        created_count = 0
        updated_count = 0
        
        for attendant in attendants:
            profile, created = AttendantProfile.objects.get_or_create(
                user=attendant,
                defaults={
                    'work_days': work_days,
                    'start_time': start_time,
                    'end_time': end_time,
                }
            )
            
            if not created:
                # Update existing profile
                profile.work_days = work_days
                profile.start_time = start_time
                profile.end_time = end_time
                profile.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Updated schedule for {attendant.get_full_name()}: {", ".join(work_days)}, {start_time.strftime("%I:%M %p")} - {end_time.strftime("%I:%M %p")}')
                )
            else:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created schedule for {attendant.get_full_name()}: {", ".join(work_days)}, {start_time.strftime("%I:%M %p")} - {end_time.strftime("%I:%M %p")}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted! Created {created_count} profile(s), Updated {updated_count} profile(s).'
            )
        )

