# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0007_issuerassertion_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuerassertion',
            name='image',
            field=models.ImageField(default=None, upload_to=b'issued/badges', blank=True),
            preserve_default=False,
        ),
    ]
