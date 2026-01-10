from django.core.management.base import BaseCommand
from appointments.models import Appointment
import uuid

class Command(BaseCommand):
    help = 'Backfill missing transaction_id on appointments. Use --only-completed to limit to completed appointments.'

    def add_arguments(self, parser):
        parser.add_argument('--only-completed', action='store_true', help='Only backfill appointments with status=completed')
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes, only report')

    def handle(self, *args, **options):
        only_completed = options.get('only_completed')
        dry_run = options.get('dry_run')

        qs = Appointment.objects.filter(transaction_id__isnull=True)
        qs = qs | Appointment.objects.filter(transaction_id='')
        qs = qs.distinct()

        if only_completed:
            qs = qs.filter(status='completed')

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No appointments without transaction_id found.'))
            return

        self.stdout.write(f'Found {total} appointments without transaction_id (only_completed={only_completed}).')
        changed = 0
        for appt in qs.iterator():
            # generate unique id
            tid = str(uuid.uuid4())[:8].upper()
            # avoid collisions
            while Appointment.objects.filter(transaction_id=tid).exists():
                tid = str(uuid.uuid4())[:8].upper()

            self.stdout.write(f'Appointment #{appt.id}: assigning {tid}')
            if not dry_run:
                appt.transaction_id = tid
                appt.save(update_fields=['transaction_id'])
            changed += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Assigned transaction_id to {changed} appointments.'))