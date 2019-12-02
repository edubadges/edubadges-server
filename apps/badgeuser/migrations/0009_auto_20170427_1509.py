# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0008_auto_20170427_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeuser',
            name='entity_id',
            field=models.CharField(default=None, unique=True, max_length=254),
            preserve_default=True,
        ),
    ]
