# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('local_components', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='badgeclass',
            options={},
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='errors',
            field=jsonfield.fields.JSONField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='url',
            field=models.URLField(default='', max_length=1024, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='errors',
            field=jsonfield.fields.JSONField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='recipient_id',
            field=models.CharField(default='', max_length=1024),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='url',
            field=models.URLField(default='', max_length=1024, blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuer',
            name='errors',
            field=jsonfield.fields.JSONField(default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuer',
            name='url',
            field=models.URLField(default='', max_length=1024, blank=True),
            preserve_default=False,
        ),
    ]
