# Generated by Django 3.1.3 on 2021-03-04 19:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_api', '0040_project_loading_gtfs_job_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='calendar',
            name='end_date',
            field=models.DateField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='friday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='monday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='saturday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='start_date',
            field=models.DateField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='sunday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='thursday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='tuesday',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='calendar',
            name='wednesday',
            field=models.BooleanField(default=False),
        ),
    ]
