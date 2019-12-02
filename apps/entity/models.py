# encoding: utf-8


import cachemodel
from django.db import models

from mainsite.utils import generate_entity_uri


class _AbstractVersionedEntity(cachemodel.CacheModel):
    entity_version = models.PositiveIntegerField(blank=False, null=False, default=1)

    class Meta:
        abstract = True

    def get_entity_class_name(self):
        if hasattr(self, 'entity_class_name') and self.entity_class_name:
            return self.entity_class_name
        return self.__class__.__name__

    def save(self, *args, **kwargs):
        if self.entity_id is None:
            self.entity_id = generate_entity_uri()

        self.entity_version += 1
        return super(_AbstractVersionedEntity, self).save(*args, **kwargs)

    def publish(self):
        super(_AbstractVersionedEntity, self).publish()
        self.publish_by('entity_id')

    def delete(self, *args, **kwargs):
        self.publish_delete('entity_id')
        return super(_AbstractVersionedEntity, self).delete(*args, **kwargs)


class _MigratingToBaseVersionedEntity(_AbstractVersionedEntity):
    """
    A temporary abstract model that exists to provide a migration path for existing models to BaseVersionedEntity.

    Usage:
       1.) change ExistingModel to subclass from _MigratingToBaseVersionedEntity
       2.) ./manage.py makemigrations existing_app  # existing_app.ExistingModel should get a migration that adds entity fields, default=None
       3.) ./manage.py makemigrations existing_app --empty  # build a data migration that will populate the new fields:
       example:
            operations = [
                entity.db.migrations.PopulateEntityIdsMigration('existing_app', 'ExistingModel'),
            ]   
       4.) change ExistingModel to subclass from BaseVersionedEntity instead of _MigratingToBaseVersionedEntity
       5.) ./manage.py makemigrations existing_app  # make migration that sets unique=True 
        
    """
    entity_id = models.CharField(max_length=254, blank=False, null=True, default=None)

    class Meta:
        abstract = True


class BaseVersionedEntity(_AbstractVersionedEntity):
    entity_id = models.CharField(max_length=254, unique=True, default=None)  # default=None is required

    class Meta:
        abstract = True

    def __unicode__(self):
        try:
            return '{}{}'.format(type(self)._meta.object_name, self.entity_id)
        except AttributeError:
            return self.entity_id
