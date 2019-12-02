# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0002_cachedemailaddress'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='badgeuser',
            options={'verbose_name': 'badge user', 'verbose_name_plural': 'badge users'},
        ),
    ]
