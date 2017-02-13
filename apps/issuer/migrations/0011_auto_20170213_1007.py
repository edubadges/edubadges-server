# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0010_auto_20170120_1724'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='criteria_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='description',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='description',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='email',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
    ]
