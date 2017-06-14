# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0005_badgrapp_ui_login_redirect'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgrapp',
            name='ui_signup_success_redirect',
            field=models.URLField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgrapp',
            name='ui_login_redirect',
            field=models.URLField(null=True),
            preserve_default=True,
        ),
    ]
