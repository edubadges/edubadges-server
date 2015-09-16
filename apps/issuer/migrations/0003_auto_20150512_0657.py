# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0002_auto_20150409_1200'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='badgeclass',
            options={'verbose_name_plural': 'Badge classes'},
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='image',
            field=models.ImageField(upload_to=b'issued', blank=True),
            preserve_default=True,
        ),
    ]
