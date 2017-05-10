# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0008_auto_20170509_1531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipientgroup',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='recipientgroup',
            name='updated_by',
        ),
        migrations.AlterField(
            model_name='recipientgroup',
            name='created_by',
            field=models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
