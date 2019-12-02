# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0002_badgrapp'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emailblacklist',
            options={'verbose_name': 'Blacklisted email', 'verbose_name_plural': 'Blacklisted emails'},
        ),
    ]
