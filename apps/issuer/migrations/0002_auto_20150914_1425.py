# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
    ]
