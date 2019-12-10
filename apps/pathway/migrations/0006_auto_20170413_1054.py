# -*- coding: utf-8 -*-


import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0005_auto_20170217_1104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pathway',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'populate_slug', unique=True, max_length=254, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pathwayelement',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'name', unique=True, max_length=254, editable=False),
            preserve_default=True,
        ),
    ]
