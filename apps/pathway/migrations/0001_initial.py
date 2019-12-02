# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
import jsonfield.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0007_auto_20151117_1555'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pathway',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('issuer', models.ForeignKey(to='issuer.Issuer', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PathwayElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=254)),
                ('description', models.TextField()),
                ('alignment_url', models.URLField(null=True, blank=True)),
                ('completion_requirements', jsonfield.fields.JSONField(null=True, blank=True)),
                ('completion_badgeclass', models.ForeignKey(blank=True, to='issuer.BadgeClass', null=True, on_delete=models.SET_NULL)),
                ('created_by', models.ForeignKey(related_name='pathwayelement_created', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('parent_element', models.ForeignKey(blank=True, to='pathway.PathwayElement', null=True, on_delete=models.SET_NULL)),
                ('pathway', models.ForeignKey(to='pathway.Pathway', on_delete=models.CASCADE)),
                ('updated_by', models.ForeignKey(related_name='pathwayelement_updated', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PathwayElementBadge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('badgeclass', models.ForeignKey(to='issuer.BadgeClass', on_delete=models.CASCADE)),
                ('element', models.ForeignKey(to='pathway.PathwayElement', on_delete=models.CASCADE)),
                ('pathway', models.ForeignKey(to='pathway.Pathway', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='pathway',
            name='root_element',
            field=models.OneToOneField(related_name='toplevel_pathway', null=True, to='pathway.PathwayElement', on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
