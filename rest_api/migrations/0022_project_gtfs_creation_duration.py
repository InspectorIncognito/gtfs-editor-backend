# Generated by Django 3.1.3 on 2020-11-20 15:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0021_remove_project_gtfs_creation_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='gtfs_creation_duration',
            field=models.DurationField(default=None, null=True),
        ),
    ]
