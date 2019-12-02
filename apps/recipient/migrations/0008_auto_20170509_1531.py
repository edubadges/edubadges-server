# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0007_auto_20170509_1529'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipientgroup',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='recipientgroupmembership',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='recipientprofile',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
        ),
    ]
