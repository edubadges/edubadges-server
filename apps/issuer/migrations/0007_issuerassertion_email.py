# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0006_auto_20150331_1454'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuerassertion',
            name='email',
            field=models.EmailField(default='test@example.com', max_length=255),
            preserve_default=False,
        ),
    ]
