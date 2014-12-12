# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issuer', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuer',
            name='owner_user',
            field=models.ForeignKey(related_name='owner', on_delete=django.db.models.deletion.PROTECT, default=1, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
