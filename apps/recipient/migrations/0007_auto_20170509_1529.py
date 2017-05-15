# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import entity


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0006_auto_20170509_1529'),
    ]

    operations = [
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientProfile'),
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientGroup'),
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientGroupMembership'),
    ]
