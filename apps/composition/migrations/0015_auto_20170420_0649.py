# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0014_auto_20170413_1054'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='localbadgeclass',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='localbadgeclass',
            name='issuer',
        ),
        migrations.RemoveField(
            model_name='localissuer',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='local_badgeclass',
        ),
        migrations.DeleteModel(
            name='LocalBadgeClass',
        ),
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='local_issuer',
        ),
        migrations.DeleteModel(
            name='LocalIssuer',
        ),
    ]
