# Generated by Django 3.2.24 on 2024-07-19 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0021_systemnotification_title'),
    ]

    operations = [
        migrations.RenameField(
            model_name='systemnotification',
            old_name='notification',
            new_name='notification_en',
        ),
        migrations.AddField(
            model_name='systemnotification',
            name='notification_nl',
            field=models.TextField(default=None),
        ),
        migrations.AlterField(
            model_name='systemnotification',
            name='display_end',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='systemnotification',
            name='display_start',
            field=models.DateTimeField(),
        ),
    ]