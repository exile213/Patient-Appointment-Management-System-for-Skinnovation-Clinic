# Data migration to auto-link existing packages to services by name matching

from django.db import migrations
from django.db.models import Q
import re


def link_packages_to_services(apps, schema_editor):
    """Auto-link existing packages to services based on name matching"""
    Package = apps.get_model('packages', 'Package')
    Service = apps.get_model('services', 'Service')
    PackageService = apps.get_model('packages', 'PackageService')
    
    # Get all non-archived packages
    packages = Package.objects.filter(archived=False)
    
    for package in packages:
        # Extract service name from package name by removing "3 + 1" or similar prefix
        package_name_clean = package.package_name
        # Remove patterns like "3 + 1 " at the start
        package_name_clean = re.sub(r'^\d+\s*\+\s*\d+\s+', '', package_name_clean).strip()
        
        # Try to find matching service (case-insensitive)
        try:
            service = Service.objects.get(
                Q(service_name__iexact=package_name_clean) &
                Q(archived=False)
            )
            # Create PackageService relationship
            PackageService.objects.get_or_create(
                package=package,
                service=service
            )
            print(f"✓ Linked package '{package.package_name}' to service '{service.service_name}'")
        except Service.DoesNotExist:
            # Try partial matching as fallback
            try:
                service = Service.objects.filter(
                    service_name__icontains=package_name_clean.split()[0],
                    archived=False
                ).first()
                if service:
                    PackageService.objects.get_or_create(
                        package=package,
                        service=service
                    )
                    print(f"✓ Linked package '{package.package_name}' to service '{service.service_name}' (partial match)")
                else:
                    print(f"✗ No matching service found for package '{package.package_name}'")
            except Exception as e:
                print(f"✗ Error linking package '{package.package_name}': {str(e)}")
        except Service.MultipleObjectsReturned:
            # If multiple services match, skip this package
            print(f"✗ Multiple matching services found for package '{package.package_name}', skipped")
        except Exception as e:
            print(f"✗ Error processing package '{package.package_name}': {str(e)}")


def reverse_link_packages_to_services(apps, schema_editor):
    """Reverse migration - remove all PackageService relationships"""
    PackageService = apps.get_model('packages', 'PackageService')
    PackageService.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0004_package_services_through_model'),
    ]

    operations = [
        migrations.RunPython(link_packages_to_services, reverse_link_packages_to_services),
    ]
