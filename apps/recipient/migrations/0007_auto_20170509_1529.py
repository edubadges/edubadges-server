# -*- coding: utf-8 -*-


import entity
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0006_auto_20170509_1529'),
    ]

    operations = [
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientProfile'),
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientGroup'),
        entity.db.migrations.PopulateEntityIdsMigration('recipient', 'RecipientGroupMembership'),
    ]
