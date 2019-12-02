# -*- coding: utf-8 -*-


from django.db import models, migrations
import autoslug.fields


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
