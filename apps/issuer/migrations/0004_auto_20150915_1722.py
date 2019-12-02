# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0003_auto_20150512_0657'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='recipient_identifier',
            field=models.EmailField(default='', max_length=1024),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='issuer',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='badgeclass',
            field=models.ForeignKey(related_name='badgeinstances', on_delete=django.db.models.deletion.PROTECT, to='issuer.BadgeClass'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='image',
            field=models.ImageField(upload_to=b'uploads/badges', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='issuer',
            field=models.ForeignKey(to='issuer.Issuer'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='image',
            field=models.ImageField(null=True, upload_to=b'uploads/issuers', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='owner',
            field=models.ForeignKey(related_name='issuers', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
