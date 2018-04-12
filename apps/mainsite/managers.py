# Created by wiggins@concentricsky.com on 4/18/16.
import cachemodel
from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404

from mainsite.utils import OriginSetting


class SlugOrJsonIdCacheModelManager(cachemodel.CacheModelManager):
    def __init__(self, slug_kwarg_name='slug', slug_field_name='slug'):
        super(SlugOrJsonIdCacheModelManager, self).__init__()
        self.slug_kwarg_name = slug_kwarg_name
        self.slug_field_name = slug_field_name

    def get_slug_kwarg_name(self):
        return self.slug_kwarg_name

    def get_by_slug_or_id(self, slug):
        if slug.startswith(OriginSetting.HTTP):
            path = slug[len(OriginSetting.HTTP):]
            try:
                r = resolve(path)
                slug = r.kwargs.get(self.get_slug_kwarg_name())
            except Resolver404 as e:
                raise self.model.DoesNotExist
        return self.get(**{self.slug_field_name: slug})

    def get_by_slug_or_entity_id_or_id(self, slug):
        if slug.startswith(OriginSetting.HTTP):
            path = slug[len(OriginSetting.HTTP):]
            try:
                r = resolve(path)
                slug = r.kwargs.get(self.get_slug_kwarg_name())
            except Resolver404 as e:
                raise self.model.DoesNotExist

        return self.get_by_slug_or_entity_id(slug)

    def get_by_id(self, idstring):
        return self.get_by_slug_or_id(idstring)

    def get_by_slug_or_entity_id(self, query):
        try:
            return self.get(entity_id=query)
        except self.model.DoesNotExist:
            pass

        return self.get(slug=query)
