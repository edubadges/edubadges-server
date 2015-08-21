# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('local_components', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('slug', autoslug.fields.AutoSlugField(max_length=128)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('share_hash', models.CharField(max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CollectionPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('can_write', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(to='composer.Collection')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalBadgeInstanceCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(blank=True)),
                ('collection', models.ForeignKey(to='composer.Collection')),
                ('instance', models.ForeignKey(to='local_components.BadgeInstance')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='localbadgeinstancecollection',
            unique_together=set([('instance', 'collection')]),
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([('user', 'collection')]),
        ),
        migrations.AddField(
            model_name='collection',
            name='instances',
            field=models.ManyToManyField(to='local_components.BadgeInstance', through='composer.LocalBadgeInstanceCollection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='owner',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='shared_with',
            field=models.ManyToManyField(related_name='shared_with_me', through='composer.CollectionPermission', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=set([('owner', 'slug')]),
        ),
    ]
