# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0004_auto_20170120_1724'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgrapp',
            name='ui_login_redirect',
            field=models.URLField(default='https://badgr.io/'),
            preserve_default=False,
        ),
    ]
