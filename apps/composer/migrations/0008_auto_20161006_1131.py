# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0007_auto_20150914_1711'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='collection',
            name='instances',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='shared_with',
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='collectionpermission',
            name='collection',
        ),
        migrations.RemoveField(
            model_name='collectionpermission',
            name='user',
        ),
        migrations.DeleteModel(
            name='CollectionPermission',
        ),
        migrations.AlterUniqueTogether(
            name='storedbadgeinstancecollection',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstancecollection',
            name='collection',
        ),
        migrations.DeleteModel(
            name='Collection',
        ),
        migrations.RemoveField(
            model_name='storedbadgeinstancecollection',
            name='instance',
        ),
        migrations.DeleteModel(
            name='StoredBadgeInstanceCollection',
        ),
    ]
