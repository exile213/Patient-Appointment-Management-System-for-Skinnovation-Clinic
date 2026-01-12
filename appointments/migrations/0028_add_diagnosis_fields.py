from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0027_feedback_equipment_rating_feedback_room_rating'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagnosis',
            name='blood_pressure',
            field=models.CharField(blank=True, max_length=20, null=True, help_text='Format: 120/80'),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='skin_type',
            field=models.CharField(blank=True, max_length=3, null=True, choices=[('I', 'Type I (Very Fair)'), ('II', 'Type II (Fair)'), ('III', 'Type III (Medium)'), ('IV', 'Type IV (Olive)'), ('V', 'Type V (Brown)'), ('VI', 'Type VI (Black)')]),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='lesion_type',
            field=models.CharField(blank=True, max_length=20, null=True, choices=[('warts', 'Warts'), ('moles', 'Moles'), ('skin_tags', 'Skin Tags'), ('syringoma', 'Syringoma'), ('milia', 'Milia'), ('other', 'Other')]),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='target_area',
            field=models.CharField(blank=True, max_length=20, null=True, choices=[('face', 'Face'), ('neck', 'Neck'), ('chest', 'Chest/Torso'), ('back', 'Back'), ('limbs', 'Arms/Legs')]),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='keloid_risk',
            field=models.CharField(blank=True, max_length=3, null=True, choices=[('yes', 'Yes'), ('no', 'No')]),
        ),
        migrations.AddField(
            model_name='diagnosis',
            name='accutane_history',
            field=models.CharField(blank=True, max_length=10, null=True, choices=[('yes_6m', 'Yes (Last 6 months)'), ('no', 'No')]),
        ),
    ]
