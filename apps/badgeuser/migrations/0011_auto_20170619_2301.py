# -*- coding: utf-8 -*-


import badgeuser.managers
from django.db import migrations


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
