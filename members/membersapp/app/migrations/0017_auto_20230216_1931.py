# Generated by Django 3.2 on 2023-02-16 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_members_ismember'),
    ]

    operations = [
        migrations.AddField(
            model_name='applications',
            name='emailcheck_date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='applications',
            name='validemail',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='applications',
            name='validemail_date',
            field=models.DateField(null=True),
        ),
    ]
