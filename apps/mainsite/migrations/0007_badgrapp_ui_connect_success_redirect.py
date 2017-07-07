# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0006_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgrapp',
            name='ui_connect_success_redirect',
            field=models.URLField(null=True),
        ),
    ]
