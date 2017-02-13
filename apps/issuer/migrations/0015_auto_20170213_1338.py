# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0014_auto_20170213_1026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='badgeclass',
            old_name='json',
            new_name='old_json',
        ),
        migrations.RenameField(
            model_name='badgeinstance',
            old_name='json',
            new_name='old_json',
        ),
        migrations.RenameField(
            model_name='issuer',
            old_name='json',
            new_name='old_json',
        ),
        migrations.RemoveField(
            model_name='badgeclass',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='badgeinstance',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='identifier',
        ),
    ]
