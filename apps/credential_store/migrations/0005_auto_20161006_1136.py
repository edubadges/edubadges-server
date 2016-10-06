# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credential_store', '0004_auto_20150914_2125'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storedbadgeclass',
            name='issuer',
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstance',
            name='badgeclass',
        ),
        migrations.DeleteModel(
            name='StoredBadgeClass',
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstance',
            name='issuer',
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstance',
            name='recipient_user',
        ),
        migrations.DeleteModel(
            name='StoredBadgeInstance',
        ),
        migrations.DeleteModel(
            name='StoredIssuer',
        ),
    ]
