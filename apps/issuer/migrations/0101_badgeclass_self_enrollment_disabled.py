# Generated by Django 2.2.26 on 2022-08-16 08:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0100_auto_20220509_1338'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='self_enrollment_disabled',
            field=models.BooleanField(default=False),
        ),
    ]
