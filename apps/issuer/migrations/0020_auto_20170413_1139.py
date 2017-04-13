# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from mainsite.utils import generate_entity_uri


def noop(apps, schema_editor):
    pass


def assign_missing_entity_ids(apps, schema_editor):
    _give_existing_objects_entity_ids(apps.get_model('issuer', 'Issuer'), 'Issuer')
    _give_existing_objects_entity_ids(apps.get_model('issuer', 'BadgeClass'), 'BadgeClass')
    _give_existing_objects_entity_ids(apps.get_model('issuer', 'BadgeInstance'), 'Assertion')


def _give_existing_objects_entity_ids(model_cls, entity_class_name):
    for obj in model_cls.objects.all():
        if obj.entity_id is None:
            obj.entity_id = generate_entity_uri(entity_class_name)
            obj.save(force_update=True)


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0019_auto_20170413_1136'),
    ]

    operations = [
        migrations.RunPython(assign_missing_entity_ids, reverse_code=noop),
    ]



