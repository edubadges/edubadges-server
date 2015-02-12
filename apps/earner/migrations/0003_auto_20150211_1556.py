# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('earner', '0002_auto_20150115_1225'),
    ]

    operations = [
        migrations.AlterField(
            model_name='earnerbadge',
            name='badge',
            field=models.OneToOneField(related_name='earnerbadge', null=True, to='badgeanalysis.OpenBadge'),
            preserve_default=True,
        ),
    ]
