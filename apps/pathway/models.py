# Created by wiggins@concentricsky.com on 3/30/16.
import cachemodel
import basic_models
from django.db import models
from jsonfield import JSONField


class Pathway(cachemodel.CacheModel):
    issuer = models.ForeignKey('issuer.Issuer')
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


class PathwayElement(basic_models.DefaultModel):
    pathway = models.ForeignKey('pathway.Pathway')
    parent_element = models.ForeignKey('pathway.PathwayElement', blank=True, null=True)
    name = models.CharField(max_length=254)
    description = models.TextField()
    alignment_url = models.URLField(blank=True, null=True)
    completion_badgeclass = models.ForeignKey('issuer.BadgeClass', blank=True, null=True)
    completion_requirements = JSONField(blank=True, null=True)


class PathwayElementBadge(cachemodel.CacheModel):
    pathway = models.ForeignKey('pathway.Pathway')
    element = models.ForeignKey('pathway.PathwayElement')
    badgeclass = models.ForeignKey('issuer.BadgeClass')
