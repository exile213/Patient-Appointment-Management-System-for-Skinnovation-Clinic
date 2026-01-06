from django.core.management.base import BaseCommand
from appointments.models import TimeSlot
from datetime import time


class Command(BaseCommand):
    help = 'Create default time slots for appointments (10:00 AM to 5:00 PM)'

    def handle(self, *args, **kwargs):
        # Default time slots from 10:00 AM to 5:00 PM
        default_times = [
            time(10, 0),   # 10:00 AM
            time(10, 30),  # 10:30 AM
            time(11, 0),   # 11:00 AM
            time(11, 30),  # 11:30 AM
            time(12, 0),   # 12:00 PM
            time(12, 30),  # 12:30 PM
            time(13, 0),   # 1:00 PM
            time(13, 30),  # 1:30 PM
            time(14, 0),   # 2:00 PM
            time(14, 30),  # 2:30 PM
            time(15, 0),   # 3:00 PM
            time(15, 30),  # 3:30 PM
            time(16, 0),   # 4:00 PM
            time(16, 30),  # 4:30 PM
            time(17, 0),   # 5:00 PM
        ]
        
        created_count = 0
        for slot_time in default_times:
            time_slot, created = TimeSlot.objects.get_or_create(
                time=slot_time,
                defaults={'is_active': True}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created time slot: {slot_time.strftime("%I:%M %p")}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Time slot already exists: {slot_time.strftime("%I:%M %p")}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal time slots created: {created_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total time slots in database: {TimeSlot.objects.count()}')
        )
