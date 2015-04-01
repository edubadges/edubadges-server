# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0008_issuerassertion_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuerassertion',
            name='revocation_reason',
            field=models.CharField(default=None, max_length=255, blank=True, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuerassertion',
            name='revoked',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
