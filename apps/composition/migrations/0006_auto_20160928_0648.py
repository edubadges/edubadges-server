# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0005_auto_20151117_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='localbadgeclass',
            name='image_preview_status',
            field=models.IntegerField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localissuer',
            name='image_preview_status',
            field=models.IntegerField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
