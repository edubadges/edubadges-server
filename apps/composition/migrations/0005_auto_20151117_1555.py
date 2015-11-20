# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0004_auto_20150915_1057'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='localbadgeclass',
            options={'verbose_name': 'local badge class', 'verbose_name_plural': 'local badge classes'},
        ),
        migrations.AlterField(
            model_name='localbadgeclass',
            name='image',
            field=models.FileField(upload_to=b'uploads/badges', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localbadgeinstance',
            name='image',
            field=models.FileField(upload_to=b'uploads/badges', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localissuer',
            name='image',
            field=models.FileField(null=True, upload_to=b'uploads/issuers', blank=True),
            preserve_default=True,
        ),
    ]
