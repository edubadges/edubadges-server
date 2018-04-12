# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0003_auto_20160901_1537'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgrapp',
            name='name',
            field=models.CharField(default='Badgr', max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgrapp',
            name='signup_redirect',
            field=models.URLField(default='https://badgr.io/signup'),
            preserve_default=False,
        ),
    ]
