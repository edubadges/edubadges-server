# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0002_auto_20141124_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='openbadge',
            name='full_ld_expanded',
            field=jsonfield.fields.JSONField(),
            preserve_default=False,
        ),
    ]
