#!/usr/bin/env python
"""Convert data_export.json to Django fixture format"""
import json

with open('data_export.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

fixtures = []

# Fields to exclude (reverse relations, computed fields)
EXCLUDE_FIELDS = {
    'attendant_profile',  # Reverse OneToOne relation from User
    'treatment',  # Reverse OneToOne relation from Appointment
    'payment',  # Reverse OneToOne relation from Appointment
}

for model_name, records in data.items():
    for record in records:
        # Extract pk/id
        pk = record.pop('id', None)
        
        # Remove excluded fields
        fields = {k: v for k, v in record.items() if k not in EXCLUDE_FIELDS}
        
        # Create fixture object
        fixture = {
            'model': model_name,
            'pk': pk,
            'fields': fields
        }
        fixtures.append(fixture)

with open('data_export_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(fixtures, f, indent=2)

print(f"✓ Converted {len(fixtures)} objects to Django fixture format")
print(f"✓ Saved to data_export_fixed.json")
