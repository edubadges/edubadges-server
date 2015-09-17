# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0002_auto_20150914_1421'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='localbadgeinstance',
            name='email',
        ),
        migrations.AddField(
            model_name='localbadgeinstance',
            name='recipient_identifier',
            field=models.EmailField(default='', max_length=1024),
            preserve_default=False,
        ),
    ]
