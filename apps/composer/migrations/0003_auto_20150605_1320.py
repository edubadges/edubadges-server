# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0002_auto_20150515_0958'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collection',
            old_name='recipient',
            new_name='owner',
        ),
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=set([('owner', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([('viewer', 'collection')]),
        ),
    ]
