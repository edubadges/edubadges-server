# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='storedbadgeinstancecollection',
            unique_together=set([('instance', 'collection')]),
        ),
    ]
