# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0010_auto_20170120_1724'),
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
            model_name='badgeinstance',
            name='evidence_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='salt',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
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
