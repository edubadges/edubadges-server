# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0005_auto_20150330_2110'),
    ]

    operations = [
        migrations.AlterField(
            model_name='issuerassertion',
            name='issuer',
            field=models.ForeignKey(related_name='assertions', to='issuer.Issuer'),
            preserve_default=True,
        ),
    ]
