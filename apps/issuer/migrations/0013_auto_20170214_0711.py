# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0012_auto_20170213_1531'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='source',
            field=models.CharField(default='local', max_length=254),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeclass',
            name='source_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='source',
            field=models.CharField(default='local', max_length=254),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issuer',
            name='source_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
            preserve_default=True,
        ),
    ]
