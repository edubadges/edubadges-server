# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StoredBadgeClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('id_hash', models.CharField(unique=True, max_length=65)),
                ('url', models.URLField(max_length=1024, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoredBadgeInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('id_hash', models.CharField(unique=True, max_length=65)),
                ('url', models.URLField(max_length=1024, blank=True)),
                ('recipient_id', models.CharField(max_length=1024)),
                ('badgeclass', models.ForeignKey(to='credential_store.StoredBadgeClass', null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StoredIssuer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('id_hash', models.CharField(unique=True, max_length=65)),
                ('url', models.URLField(max_length=1024, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='storedbadgeinstance',
            name='issuer',
            field=models.ForeignKey(to='credential_store.StoredIssuer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='storedbadgeinstance',
            name='recipient_user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='storedbadgeclass',
            name='issuer',
            field=models.ForeignKey(to='credential_store.StoredIssuer'),
            preserve_default=True,
        ),
    ]
