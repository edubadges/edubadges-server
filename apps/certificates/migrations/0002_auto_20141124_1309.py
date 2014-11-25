# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0002_auto_20141124_1300'),
        ('certificates', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificate',
            name='image',
        ),
        migrations.AddField(
            model_name='certificate',
            name='open_badge',
            field=models.ForeignKey(default=3, to='badgeanalysis.OpenBadge'),
            preserve_default=False,
        ),
    ]
