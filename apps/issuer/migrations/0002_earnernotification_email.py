# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='earnernotification',
            name='email',
            field=models.EmailField(default="notvalid@example.com", max_length=254),
            preserve_default=False,
        ),
    ]
