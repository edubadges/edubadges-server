# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('earner', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='earnerbadge',
            name='badge',
            field=models.ForeignKey(to='badgeanalysis.OpenBadge', null=True),
            preserve_default=True,
        ),
    ]
