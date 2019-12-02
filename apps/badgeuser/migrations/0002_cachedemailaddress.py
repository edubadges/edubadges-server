# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_email_max_length'),
        ('badgeuser', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CachedEmailAddress',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('account.emailaddress', models.Model),
        ),
    ]
