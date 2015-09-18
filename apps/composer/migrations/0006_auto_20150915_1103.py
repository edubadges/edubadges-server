# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0005_collection_share_hash'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='owner',
            field=models.ForeignKey(related_name='composer_collection_set', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collection',
            name='shared_with',
            field=models.ManyToManyField(related_name='composer_shared_with_me', through='composer.CollectionPermission', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='collectionpermission',
            name='user',
            field=models.ForeignKey(related_name='composer_collectionpermission_set', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
