# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('credential_store', '0002_auto_20150514_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='storedbadgeinstance',
            name='image',
            field=models.ImageField(null=True, upload_to=b'uploads/badges'),
            preserve_default=True,
        ),
    ]
