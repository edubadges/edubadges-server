# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('badgeanalysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Assertion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('iri', models.CharField(max_length=2048)),
                ('badge_object', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('notes', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BadgeClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('iri', models.CharField(max_length=2048)),
                ('badge_object', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('notes', jsonfield.fields.JSONField()),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='IssuerOrg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('iri', models.CharField(max_length=2048)),
                ('badge_object', jsonfield.fields.JSONField()),
                ('errors', jsonfield.fields.JSONField()),
                ('notes', jsonfield.fields.JSONField()),
                ('scheme', models.ForeignKey(to='badgeanalysis.BadgeScheme')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='issuerorg',
            field=models.ForeignKey(blank=True, to='badgeanalysis.IssuerOrg', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='scheme',
            field=models.ForeignKey(to='badgeanalysis.BadgeScheme'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assertion',
            name='badgeclass',
            field=models.ForeignKey(blank=True, to='badgeanalysis.BadgeClass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assertion',
            name='scheme',
            field=models.ForeignKey(to='badgeanalysis.BadgeScheme'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openbadge',
            name='assertion',
            field=models.ForeignKey(blank=True, to='badgeanalysis.Assertion', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openbadge',
            name='badgeclass',
            field=models.ForeignKey(blank=True, to='badgeanalysis.BadgeClass', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='openbadge',
            name='issuerorg',
            field=models.ForeignKey(blank=True, to='badgeanalysis.IssuerOrg', null=True),
            preserve_default=True,
        ),
    ]
