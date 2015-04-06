# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0004_auto_20150313_1604'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issuerbadgeclass',
            name='criteria_url',
        ),
        migrations.AlterField(
            model_name='issuerassertion',
            name='badgeclass',
            field=models.ForeignKey(related_name='assertions', on_delete=django.db.models.deletion.PROTECT, to='issuer.IssuerBadgeClass'),
            preserve_default=True,
        ),
    ]
