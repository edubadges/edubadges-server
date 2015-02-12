# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0002_auto_20150127_1808'),
    ]

    operations = [
        migrations.AlterField(
            model_name='openbadge',
            name='assertion',
            field=models.OneToOneField(related_name='openbadge', null=True, blank=True, to='badgeanalysis.Assertion'),
            preserve_default=True,
        ),
    ]
