# Generated by Django 3.2.4 on 2022-08-16 20:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0045_alter_trip_trip_headsign'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='loading_gtfs_error_message',
            field=models.TextField(default=None, null=True),
        ),
    ]
