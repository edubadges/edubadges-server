# -*- coding: utf-8 -*-


import autoslug.fields
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pathwayelement',
            options={'ordering': ('ordering',)},
        ),
        migrations.AddField(
            model_name='pathway',
            name='slug',
            field=autoslug.fields.AutoSlugField(default=None, unique=True, max_length=254, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pathwayelement',
            name='ordering',
            field=models.IntegerField(default=99),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pathwayelement',
            name='slug',
            field=autoslug.fields.AutoSlugField(default=None, unique=True, max_length=254, editable=False),
            preserve_default=False,
        ),
    ]
