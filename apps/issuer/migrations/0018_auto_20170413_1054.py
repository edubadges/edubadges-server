# -*- coding: utf-8 -*-


import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0017_auto_20170227_1334'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeinstance',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from='get_new_slug', unique=True, max_length=255, editable=False),
            preserve_default=True,
        ),
    ]
