# Generated by Django 3.1.3 on 2020-11-20 12:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0018_auto_20201119_1526'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='gtfs_creation_status',
            field=models.CharField(choices=[('queued', 'Queued'), ('processing', 'Processing'), ('finished', 'Finished'), ('error', 'Error')], default=None, max_length=20, null=True),
        ),
    ]
