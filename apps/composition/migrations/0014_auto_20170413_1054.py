# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0013_auto_20170227_0847'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=True, max_length=128, populate_from=b'name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localbadgeclass',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=True, unique=True, max_length=255, populate_from=b'name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localbadgeinstance',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'populate_slug', unique=True, max_length=255, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localissuer',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=True, unique=True, max_length=255, populate_from=b'name'),
            preserve_default=True,
        ),
    ]
