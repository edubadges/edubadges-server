# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0023_auto_20170531_1044'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeinstance',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='badgeinstanceevidence',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
        ),
    ]
