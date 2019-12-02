# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='localbadgeinstancecollection',
            options={'verbose_name': 'BadgeInstance in a Collection', 'verbose_name_plural': 'BadgeInstances in Collections'},
        ),
        migrations.AddField(
            model_name='localbadgeclass',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localbadgeinstance',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='localissuer',
            name='identifier',
            field=models.CharField(default=b'get_full_url', max_length=1024),
            preserve_default=True,
        ),
    ]
