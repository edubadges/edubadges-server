# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from autoslug import AutoSlugField
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0016_auto_20170214_0749'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='original_json',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),

        # Reset state of populate_from kwarg for AutoSlugField after bumping django-autoslugfield to 1.9.3.  See:
        # https://github.com/neithere/django-autoslug/commit/7b6288a300fba3afa634dc2ba836398e86468d8e
        migrations.AlterField(
            model_name='badgeclass',
            name='slug',
            field=AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='slug',
            field=AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True),
            preserve_default=True,
        ),

    ]
