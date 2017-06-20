# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0005_auto_20170413_1054'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipientgroup',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='recipientgroup',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='recipientgroupmembership',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='recipientgroupmembership',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, null=True),
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='entity_version',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='recipientgroup',
            name='slug',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='recipientgroupmembership',
            name='slug',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='recipientprofile',
            name='slug',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
        ),
    ]
