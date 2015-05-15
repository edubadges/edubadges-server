# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('credential_store', '0002_auto_20150514_1544'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=128)),
                ('slug', autoslug.fields.AutoSlugField(max_length=128)),
                ('description', models.CharField(max_length=255, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CollectionPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('writeable', models.BooleanField(default=False)),
                ('collection', models.ForeignKey(to='composer.Collection')),
                ('viewer', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoredBadgeInstanceCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(blank=True)),
                ('collection', models.ForeignKey(to='composer.Collection')),
                ('instance', models.ForeignKey(to='credential_store.StoredBadgeInstance')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([('collection', 'viewer')]),
        ),
        migrations.AddField(
            model_name='collection',
            name='instances',
            field=models.ManyToManyField(to='credential_store.StoredBadgeInstance', through='composer.StoredBadgeInstanceCollection'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='recipient',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='collection',
            name='viewers',
            field=models.ManyToManyField(related_name='sharee', through='composer.CollectionPermission', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=set([('recipient', 'slug')]),
        ),
    ]
