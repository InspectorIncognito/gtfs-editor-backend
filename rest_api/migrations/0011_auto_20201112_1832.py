# Generated by Django 3.0.7 on 2020-11-12 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0010_auto_20201112_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='route',
            name='route_id',
            field=models.CharField(max_length=50),
        ),
    ]