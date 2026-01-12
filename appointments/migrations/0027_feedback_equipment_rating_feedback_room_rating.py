from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0026_create_diagnosis'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            ALTER TABLE feedback
            ADD COLUMN IF NOT EXISTS equipment_rating integer;
            """,
            reverse_sql="""
            ALTER TABLE feedback
            DROP COLUMN IF EXISTS equipment_rating;
            """,
        ),
        migrations.RunSQL(
            sql="""
            ALTER TABLE feedback
            ADD COLUMN IF NOT EXISTS room_rating integer;
            """,
            reverse_sql="""
            ALTER TABLE feedback
            DROP COLUMN IF EXISTS room_rating;
            """,
        ),
    ]
