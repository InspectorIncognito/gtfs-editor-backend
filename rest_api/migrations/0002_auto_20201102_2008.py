# Generated by Django 3.0.7 on 2020-11-02 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trip',
            name='direction_id',
            field=models.BooleanField(null=True),
        ),
    ]
