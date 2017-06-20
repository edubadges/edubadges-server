# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from entity.db.migrations import PopulateEntityIdsMigration
from mainsite.utils import generate_entity_uri


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0006_auto_20161128_0938'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeuser',
            name='entity_id',
            field=models.CharField(default=None, null=True, max_length=254),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeuser',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        PopulateEntityIdsMigration('badgeuser', 'BadgeUser')
    ]
