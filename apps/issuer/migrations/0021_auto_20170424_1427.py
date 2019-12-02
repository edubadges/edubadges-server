# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0020_auto_20170413_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeclass',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
            preserve_default=True,
        ),
    ]
