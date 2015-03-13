# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0003_auto_20150311_1346'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuerbadgeclass',
            name='issuer',
            field=models.ForeignKey(related_name='badgeclasses', on_delete=django.db.models.deletion.PROTECT, to='issuer.Issuer'),
            preserve_default=True,
        ),
    ]
