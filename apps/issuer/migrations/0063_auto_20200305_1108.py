# Generated by Django 2.2.9 on 2020-03-05 19:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0062_auto_20200305_0713'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeclass',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='badgeinstance',
            name='slug',
        ),
    ]