#!/usr/bin/env python
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beauty_clinic_django.settings')
django.setup()

from django.test import RequestFactory
from analytics.views import analytics_api
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a fake request
factory = RequestFactory()
request = factory.get('/analytics/api/', {'date_range': '30'})

# Get an admin user
admin = User.objects.filter(user_type='admin').first()
if not admin:
    admin = User.objects.filter(user_type='owner').first()

request.user = admin

# Call the API
response = analytics_api(request)
data = json.loads(response.content)

print(f"API Response:")
print(f"Date range: {data['date_range']}")
print(f"Number of data points: {len(data['data'])}")
print(f"\nFirst 5 data points:")
for item in data['data'][:5]:
    print(f"  {item['name']}: {item['appointments']} appointments, {item['completed']} completed, ₱{item['revenue']}")
print(f"\nLast 5 data points:")
for item in data['data'][-5:]:
    print(f"  {item['name']}: {item['appointments']} appointments, {item['completed']} completed, ₱{item['revenue']}")

print(f"\nTotal appointments in chart: {sum(item['appointments'] for item in data['data'])}")
print(f"Total completed in chart: {sum(item['completed'] for item in data['data'])}")
print(f"Total revenue in chart: ₱{sum(item['revenue'] for item in data['data'])}")
