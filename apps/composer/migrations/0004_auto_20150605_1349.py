# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('composer', '0003_auto_20150605_1320'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collectionpermission',
            old_name='writeable',
            new_name='can_write',
        ),
        migrations.RenameField(
            model_name='collectionpermission',
            old_name='viewer',
            new_name='user',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='viewers',
        ),
        migrations.AddField(
            model_name='collection',
            name='shared_with',
            field=models.ManyToManyField(related_name='shared_with_me', through='composer.CollectionPermission', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([('user', 'collection')]),
        ),
    ]
