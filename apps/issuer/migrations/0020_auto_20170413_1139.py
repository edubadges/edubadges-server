# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from entity.db.migrations import PopulateEntityIdsMigration


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0019_auto_20170413_1136'),
        ('composition', '0010_auto_20170214_0712'),
    ]

    operations = [
        PopulateEntityIdsMigration('issuer', 'Issuer'),
        PopulateEntityIdsMigration('issuer', 'BadgeClass'),
        PopulateEntityIdsMigration('issuer', 'BadgeInstance', entity_class_name='Assertion'),
    ]



