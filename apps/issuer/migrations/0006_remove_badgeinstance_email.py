# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0005_auto_20150915_1723'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeinstance',
            name='email',
        ),
    ]
