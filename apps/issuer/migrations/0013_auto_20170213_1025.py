# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0012_auto_20170213_1007'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeinstance',
            name='evidence_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='salt',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
    ]
