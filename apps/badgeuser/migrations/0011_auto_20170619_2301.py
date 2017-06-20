# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import badgeuser.managers


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0010_merge'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='badgeuser',
            managers=[
                ('objects', badgeuser.managers.BadgeUserManager()),
            ],
        ),
    ]
