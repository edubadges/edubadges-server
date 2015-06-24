# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credential_store', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='storedbadgeclass',
            name='id_hash',
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstance',
            name='id_hash',
        ),
        migrations.RemoveField(
            model_name='storedissuer',
            name='id_hash',
        ),
    ]
