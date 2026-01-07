# Generated migration for adding ManyToMany relationship between Package and Service

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('packages', '0003_alter_packageappointment_attendant'),
        ('services', '0001_initial'),  # This should match the latest services migration
    ]

    operations = [
        # Create PackageService through model
        migrations.CreateModel(
            name='PackageService',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('package', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='package_services', to='packages.package')),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_packages', to='services.service')),
            ],
            options={
                'db_table': 'package_services',
            },
        ),
        # Add ManyToMany field to Package
        migrations.AddField(
            model_name='package',
            name='services',
            field=models.ManyToManyField(blank=True, related_name='packages', through='packages.PackageService', to='services.Service'),
        ),
        # Add unique constraint on PackageService
        migrations.AlterUniqueTogether(
            name='packageservice',
            unique_together={('package', 'service')},
        ),
    ]
