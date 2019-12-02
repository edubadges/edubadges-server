# -*- coding: utf-8 -*-


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
                ('collection', models.ForeignKey(to='composition.Collection')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalBadgeClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('json', jsonfield.fields.JSONField()),
                ('criteria_text', models.TextField(null=True, blank=True)),
                ('image', models.ImageField(upload_to=b'uploads/badges', blank=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255)),
                ('created_by', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
                'verbose_name_plural': 'Badge classes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalBadgeInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('json', jsonfield.fields.JSONField()),
                ('email', models.EmailField(max_length=255)),
                ('image', models.ImageField(upload_to=b'uploads/badges', blank=True)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255, editable=False)),
                ('revoked', models.BooleanField(default=False)),
                ('revocation_reason', models.CharField(default=None, max_length=255, null=True, blank=True)),
                ('badgeclass', models.ForeignKey(related_name='badgeinstances', on_delete=django.db.models.deletion.PROTECT, to='composition.LocalBadgeClass', null=True)),
                ('created_by', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalBadgeInstanceCollection',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.TextField(blank=True)),
                ('collection', models.ForeignKey(to='composition.Collection')),
                ('instance', models.ForeignKey(to='composition.LocalBadgeInstance')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalIssuer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('json', jsonfield.fields.JSONField()),
                ('image', models.ImageField(upload_to=b'uploads/issuers', blank=True)),
                ('name', models.CharField(max_length=1024)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=255)),
                ('created_by', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='localbadgeinstancecollection',
            unique_together=set([('instance', 'collection')]),
        ),
        migrations.AddField(
            model_name='localbadgeinstance',
            name='issuer',
            field=models.ForeignKey(to='composition.LocalIssuer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localbadgeinstance',
            name='recipient_user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localbadgeclass',
            name='issuer',
            field=models.ForeignKey(related_name='badgeclasses', on_delete=django.db.models.deletion.PROTECT, to='composition.LocalIssuer'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='collectionpermission',
            unique_together=set([('user', 'collection')]),
        ),
        migrations.AddField(
            model_name='collection',
            name='instances',
            field=models.ManyToManyField(to='composition.LocalBadgeInstance', through='composition.LocalBadgeInstanceCollection'),
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
            field=models.ManyToManyField(related_name='shared_with_me', through='composition.CollectionPermission', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='collection',
            unique_together=set([('owner', 'slug')]),
        ),
    ]
