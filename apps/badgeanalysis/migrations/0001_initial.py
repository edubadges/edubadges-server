# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import jsonfield.fields
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeSchemaValidator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('validates_type', models.CharField(max_length=2048)),
                ('validation_schema', models.URLField(max_length=2048, verbose_name=b'URL location of the validation schema')),
                ('schema_json', jsonfield.fields.JSONField(blank=True)),
                ('created_by', models.ForeignKey(related_name='badgeschemavalidator_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BadgeScheme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=1024)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255, blank=True)),
                ('default_type', models.CharField(max_length=64)),
                ('context_url', models.URLField(max_length=2048, verbose_name=b'URL location of the JSON-LD context file core to this scheme')),
                ('description', models.TextField(blank=True)),
                ('context_json', jsonfield.fields.JSONField(blank=True)),
                ('created_by', models.ForeignKey(related_name='badgescheme_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('updated_by', models.ForeignKey(related_name='badgescheme_updated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OpenBadge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(upload_to=b'uploads/badges/received', blank=True)),
                ('badge_input', models.TextField(null=True, blank=True)),
                ('recipient_input', models.CharField(max_length=2048, blank=True)),
                ('full_badge_object', jsonfield.fields.JSONField()),
                ('full_ld_expanded', jsonfield.fields.JSONField()),
                ('verify_method', models.CharField(max_length=48, blank=True)),
                ('errors', jsonfield.fields.JSONField()),
                ('notes', jsonfield.fields.JSONField()),
                ('created_by', models.ForeignKey(related_name='openbadge_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('scheme', models.ForeignKey(blank=True, to='badgeanalysis.BadgeScheme', null=True)),
                ('updated_by', models.ForeignKey(related_name='openbadge_updated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='badgeschemavalidator',
            name='scheme',
            field=models.ForeignKey(related_name='schemes', to='badgeanalysis.BadgeScheme'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeschemavalidator',
            name='updated_by',
            field=models.ForeignKey(related_name='badgeschemavalidator_updated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
