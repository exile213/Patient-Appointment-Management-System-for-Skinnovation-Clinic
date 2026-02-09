from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0026_create_diagnosis'),
    ]

    operations = [
        # Operations moved to 0030_feedback_equipment_rating_feedback_room_rating.py
        # to ensure correct state tracking and handle existing columns
    ]
