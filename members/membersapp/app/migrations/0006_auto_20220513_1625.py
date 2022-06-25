# Generated by Django 3.2 on 2022-05-13 16:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_alter_members_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='members',
            name='password',
        ),
        migrations.AlterField(
            model_name='applications',
            name='comment',
            field=models.TextField(null=True, verbose_name='Mgr Comments'),
        ),
        migrations.AlterField(
            model_name='applications',
            name='contrib',
            field=models.TextField(null=True, verbose_name='Contributions'),
        ),
        migrations.AlterField(
            model_name='applications',
            name='manager_date',
            field=models.DateTimeField(null=True, verbose_name='Date Approved'),
        ),
        migrations.AlterField(
            model_name='members',
            name='sub_private',
            field=models.BooleanField(default=False, verbose_name='Subscribe to spi-private?'),
        ),
    ]
