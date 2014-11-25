# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='openbadge',
            name='name',
        ),
        migrations.RemoveField(
            model_name='openbadge',
            name='slug',
        ),
    ]
