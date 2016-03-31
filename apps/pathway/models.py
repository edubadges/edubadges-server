# Created by wiggins@concentricsky.com on 3/30/16.
import uuid

import cachemodel
import basic_models
from autoslug import AutoSlugField
from django.db import models
from jsonfield import JSONField


class Pathway(cachemodel.CacheModel):
    issuer = models.ForeignKey('issuer.Issuer')
    slug = AutoSlugField(max_length=254, populate_from='populate_slug', unique=True, blank=False)
    root_element = models.OneToOneField('pathway.PathwayElement', related_name='toplevel_pathway', null=True)

    def publish(self):
        super(Pathway, self).publish()
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        issuer = self.issuer
        ret = super(Pathway, self).delete(*args, **kwargs)
        issuer.publish()
        return ret

    @property
    def cached_root_element(self):
        return PathwayElement.cached.get(pk=self.root_element_id)

    def populate_slug(self):
        return getattr(self, 'name_hint', str(uuid.uuid4()))

    def save(self, *args, **kwargs):
        name_hint = kwargs.pop('name_hint', None)
        if name_hint:
            self.name_hint = name_hint
        return super(Pathway, self).save(*args, **kwargs)


class PathwayElement(basic_models.DefaultModel):
    slug = AutoSlugField(max_length=254, populate_from='populate_slug', unique=True, blank=False)
    pathway = models.ForeignKey('pathway.Pathway')
    parent_element = models.ForeignKey('pathway.PathwayElement', blank=True, null=True)
    name = models.CharField(max_length=254)
    ordering = models.IntegerField(default=99)
    description = models.TextField()
    alignment_url = models.URLField(blank=True, null=True)
    completion_badgeclass = models.ForeignKey('issuer.BadgeClass', blank=True, null=True)
    completion_requirements = JSONField(blank=True, null=True)

    class Meta:
        ordering = ('ordering',)

    def populate_slug(self):
        return u'{}-{}'.format(self.pathway.slug, self.name)


class PathwayElementBadge(cachemodel.CacheModel):
    pathway = models.ForeignKey('pathway.Pathway')
    element = models.ForeignKey('pathway.PathwayElement')
    badgeclass = models.ForeignKey('issuer.BadgeClass')
