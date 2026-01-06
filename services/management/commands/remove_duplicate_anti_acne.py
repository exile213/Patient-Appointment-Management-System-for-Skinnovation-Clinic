from django.core.management.base import BaseCommand
from services.models import Service


class Command(BaseCommand):
    help = 'Remove duplicate Anti-Acne Treatment service'

    def handle(self, *args, **options):
        # Find all Anti-Acne Treatment services
        anti_acne_services = Service.objects.filter(service_name='Anti-Acne Treatment')
        
        if anti_acne_services.count() > 1:
            self.stdout.write(f'Found {anti_acne_services.count()} Anti-Acne Treatment services')
            
            # Keep the first one (ID: 25) and remove the duplicate (ID: 43)
            services_to_keep = anti_acne_services.first()
            services_to_remove = anti_acne_services.exclude(id=services_to_keep.id)
            
            for service in services_to_remove:
                self.stdout.write(f'Removing duplicate service: ID {service.id}, Image: {service.image}')
                service.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully removed {services_to_remove.count()} duplicate Anti-Acne Treatment service(s)'
                )
            )
        else:
            self.stdout.write('No duplicate Anti-Acne Treatment services found')


