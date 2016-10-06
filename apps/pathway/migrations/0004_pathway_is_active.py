# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0003_auto_20160415_1030'),
    ]

    operations = [
        migrations.AddField(
            model_name='pathway',
            name='is_active',
            field=models.BooleanField(default=True, db_index=True),
            preserve_default=True,
        ),
    ]
