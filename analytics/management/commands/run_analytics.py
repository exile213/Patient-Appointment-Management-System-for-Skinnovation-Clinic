from django.core.management.base import BaseCommand
from analytics.services import AnalyticsService


class Command(BaseCommand):
    help = 'Run analytics calculations for all data'

    def handle(self, *args, **options):
        self.stdout.write('Starting analytics calculations...')
        
        try:
            AnalyticsService.run_all_analytics()
            self.stdout.write(
                self.style.SUCCESS('Analytics calculations completed successfully!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running analytics: {str(e)}')
            )
