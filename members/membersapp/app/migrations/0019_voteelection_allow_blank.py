# Generated by Django 4.2 on 2025-06-15 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0018_alter_applications_comment_alter_applications_member_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="voteelection",
            name="allow_blank",
            field=models.BooleanField(default=True, verbose_name="Allow blank votes"),
        ),
    ]
