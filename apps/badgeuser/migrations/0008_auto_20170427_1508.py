# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from mainsite.base import PopulateEntityIdsMigration


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0007_auto_20170427_0957'),
    ]

    operations = [
        PopulateEntityIdsMigration('badgeuser', 'BadgeUser'),
    ]
