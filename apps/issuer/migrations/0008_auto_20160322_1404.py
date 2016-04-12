# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0007_auto_20151117_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeclass',
            name='issuer',
            field=models.ForeignKey(related_name='badgeclasses', to='issuer.Issuer'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='badgeclass',
            field=models.ForeignKey(related_name='badgeinstances', to='issuer.BadgeClass'),
            preserve_default=True,
        ),
    ]
