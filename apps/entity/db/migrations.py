# encoding: utf-8
from __future__ import unicode_literals

from django.db.migrations import RunPython

from mainsite.utils import generate_entity_uri


class PopulateEntityIdsMigration(RunPython):
    def __init__(self, app_label, model_name, entity_class_name=None, **kwargs):
        self.app_label = app_label
        self.model_name = model_name
        self.entity_class_name = entity_class_name if entity_class_name is not None else model_name
        if 'reverse_code' not in kwargs:
            kwargs['reverse_code'] = self.noop
        super(PopulateEntityIdsMigration, self).__init__(self.generate_ids, **kwargs)

    def noop(self, apps, schema_editor):
        pass

    def generate_ids(self, apps, schema_editor):
        model_cls = apps.get_model(self.app_label, self.model_name)
        for obj in model_cls.objects.all():
            if obj.entity_id is None:
                obj.entity_id = generate_entity_uri()
                obj.save(force_update=True)
