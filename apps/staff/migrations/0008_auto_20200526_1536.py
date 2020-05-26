# Generated by Django 2.2.9 on 2020-05-26 13:36

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issuer', '0069_auto_20200511_1528'),
        ('institution', '0021_populate_institution_identifier'),
        ('staff', '0007_auto_20200324_0414'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='badgeclassstaff',
            unique_together={('badgeclass', 'user')},
        ),
        migrations.AlterUniqueTogether(
            name='facultystaff',
            unique_together={('faculty', 'user')},
        ),
    ]