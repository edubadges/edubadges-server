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
        ('issuer', '0002_issuer_owner_user'),
    ]

    operations = [
        migrations.CreateModel(
            name='IssuerAssertion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('badge_object', jsonfield.fields.JSONField()),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssuerBadgeClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('badge_object', jsonfield.fields.JSONField()),
                ('name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255)),
                ('criteria_text', models.TextField(null=True, blank=True)),
                ('criteria_url', models.URLField(max_length=1024, null=True, blank=True)),
                ('image', models.ImageField(upload_to=b'uploads/badges', blank=True)),
                ('created_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('issuer', models.ForeignKey(to='issuer.Issuer', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='issuerassertion',
            name='badgeclass',
            field=models.ForeignKey(to='issuer.IssuerBadgeClass', on_delete=django.db.models.deletion.PROTECT),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuerassertion',
            name='created_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuerassertion',
            name='issuer',
            field=models.ForeignKey(to='issuer.Issuer'),
            preserve_default=True,
        ),
        migrations.RenameField(
            model_name='issuer',
            old_name='owner_user',
            new_name='owner',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='description',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='issuer_object_url',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='updated_by',
        ),
        migrations.RemoveField(
            model_name='issuer',
            name='url',
        ),
        migrations.AddField(
            model_name='issuer',
            name='badge_object',
            field=jsonfield.fields.JSONField(default=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuer',
            name='editors',
            field=models.ManyToManyField(related_name='issuers_editor_for', db_table=b'issuer_editors', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='image',
            field=models.ImageField(default=None, upload_to=b'uploads/issuers', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuer',
            name='staff',
            field=models.ManyToManyField(related_name='issuers_staff_for', db_table=b'issuer_staff', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='created_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='slug',
            field=autoslug.fields.AutoSlugField(unique=True, max_length=255),
            preserve_default=True,
        ),
    ]
