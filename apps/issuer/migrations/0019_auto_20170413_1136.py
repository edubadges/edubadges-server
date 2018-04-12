# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0018_auto_20170413_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeclass',
            name='slug',
            field=models.CharField(default=None, max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='slug',
            field=models.CharField(default=None, max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='slug',
            field=models.CharField(default=None, max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
