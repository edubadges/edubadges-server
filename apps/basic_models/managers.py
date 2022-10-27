from django.db import models


class ActiveObjectsManager(models.Manager):

    def get_queryset(self):
        return super(ActiveObjectsManager, self).get_queryset() \
            .filter(is_active=True)
