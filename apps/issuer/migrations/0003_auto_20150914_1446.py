# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0002_auto_20150914_1425'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeinstance',
            name='email',
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='recipient_identifier',
            field=models.EmailField(default='', max_length=1024),
            preserve_default=False,
        ),
    ]
