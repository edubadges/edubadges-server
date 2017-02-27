# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0016_auto_20170214_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
