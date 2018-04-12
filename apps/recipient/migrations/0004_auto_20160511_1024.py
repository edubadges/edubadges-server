# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('recipient', '0003_recipientgroup_pathways'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipientprofile',
            name='created_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 11, 17, 24, 34, 658388, tzinfo=utc), auto_now_add=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='created_by',
            field=models.ForeignKey(related_name='recipientprofile_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='is_active',
            field=models.BooleanField(default=True, db_index=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='updated_at',
            field=models.DateTimeField(default=datetime.datetime(2016, 5, 11, 17, 24, 39, 418009, tzinfo=utc), auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='recipientprofile',
            name='updated_by',
            field=models.ForeignKey(related_name='recipientprofile_updated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
