# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0023_auto_20170531_1044'),
        ('backpack', '0002_auto_20170531_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='backpackcollection',
            name='assertions',
            field=models.ManyToManyField(to='issuer.BadgeInstance', through='backpack.BackpackCollectionBadgeInstance', blank=True),
        ),
    ]
