#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from appointments.models import SMSTemplate

templates = SMSTemplate.objects.filter(template_type='attendant_reassignment')
print(f'Found {templates.count()} attendant reassignment templates')
for t in templates:
    print(f'  - {t.name}: Active={t.is_active}')

all_templates = SMSTemplate.objects.all()
print(f'\nAll templates ({all_templates.count()}):')
for t in all_templates:
    print(f'  - {t.get_template_type_display()}: {t.name} (Active={t.is_active})')
