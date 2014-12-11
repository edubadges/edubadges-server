# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0003_openbadge_full_ld_expanded'),
        ('issuer', '0002_earnernotification_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='earnernotification',
            name='badge',
            field=models.ForeignKey(blank=True, to='badgeanalysis.OpenBadge', null=True),
            preserve_default=True,
        ),
    ]
