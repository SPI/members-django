# Generated by Django 3.2 on 2022-03-28 09:45

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_auto_20220220_1125'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='members',
            managers=[
                ('object', django.db.models.manager.Manager()),
            ],
        ),
    ]
