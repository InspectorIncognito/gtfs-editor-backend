# Generated by Django 5.1.1 on 2024-09-21 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_user_password_recovery_token_user_recovery_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='username',
            field=models.CharField(max_length=30, unique=True, verbose_name='Username'),
        ),
    ]
