# Created by wiggins@concentricsky.com on 3/30/16.
import uuid

import cachemodel
import basic_models
import itertools
from autoslug import AutoSlugField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, resolve, Resolver404
from django.db import models
from jsonfield import JSONField

from issuer.models import BadgeClass, Issuer
from mainsite.managers import SlugOrJsonIdCacheModelManager


class Pathway(cachemodel.CacheModel):
    issuer = models.ForeignKey('issuer.Issuer')
    slug = AutoSlugField(max_length=254, populate_from='populate_slug', unique=True, blank=False)
    root_element = models.OneToOneField('pathway.PathwayElement', related_name='toplevel_pathway', null=True)
    # recipient_groups = reverse M2M relation to subscribed instances of recipient.RecipientGroup

    cached = SlugOrJsonIdCacheModelManager('pathway_slug')

    def publish(self):
        super(Pathway, self).publish()
        self.publish_by('slug')
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        issuer = self.issuer
        ret = super(Pathway, self).delete(*args, **kwargs)
        issuer.publish()
        return ret

    @property
    def jsonld_id(self):
        return settings.HTTP_ORIGIN+reverse('pathway_detail', kwargs={
            'issuer_slug': self.cached_issuer.slug,
            'pathway_slug': self.slug
        })

    @property
    def name(self):
        return self.cached_root_element.name

    @property
    def description(self):
        return self.cached_root_element.description

    @property
    def completion_badge(self):
        if self.cached_root_element.completion_badgeclass:
            return self.cached_root_element.completion_badgeclass

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @property
    def cached_root_element(self):
        return PathwayElement.cached.get(pk=self.root_element_id)

    @cachemodel.cached_method(auto_publish=True)
    def cached_elements(self):
        return self.pathwayelement_set.all()

    @property
    def groups(self):
        return self.recipient_groups.all()

    def cached_badgeclasses(self):
        badgeclasses = [[eb.cached_badgeclass for eb in e.cached_badges()] for e in self.cached_elements()]
        return itertools.chain.from_iterable(badgeclasses)

    def populate_slug(self):
        return getattr(self, 'name_hint', str(uuid.uuid4()))

    def save(self, *args, **kwargs):
        name_hint = kwargs.pop('name_hint', None)
        if name_hint:
            self.name_hint = name_hint
        return super(Pathway, self).save(*args, **kwargs)

    def build_element_tree(self):
        index = {}
        for element in self.cached_elements():
            index[element.jsonld_id] = element

        tree = {
            'element': self.cached_root_element,
        }

        def _build(parent, node):
            node['children'] = []
            for child in node['element'].cached_children():
                new_node = {
                    'element': child,
                }
                _build(node, new_node)
                node['children'].append(new_node)

        _build(None, tree)
        return tree


class PathwayElement(basic_models.DefaultModel):
    slug = AutoSlugField(max_length=254, populate_from='name', unique=True, blank=False)
    pathway = models.ForeignKey('pathway.Pathway')
    parent_element = models.ForeignKey('pathway.PathwayElement', blank=True, null=True)
    name = models.CharField(max_length=254)
    ordering = models.IntegerField(default=99)
    description = models.TextField()
    alignment_url = models.URLField(blank=True, null=True)
    completion_badgeclass = models.ForeignKey('issuer.BadgeClass', blank=True, null=True)
    completion_requirements = JSONField(blank=True, null=True)
    cached = SlugOrJsonIdCacheModelManager('element_slug')

    class Meta:
        ordering = ('ordering',)

    def __unicode__(self):
        return self.jsonld_id

    def save(self, *args, **kwargs):
        ret = super(PathwayElement, self).save(*args, **kwargs)
        if self.completion_requirements:
            self._update_badges_from_completion_requirements()
        return ret

    def publish(self):
        super(PathwayElement, self).publish()
        self.publish_by('slug')
        self.cached_pathway.publish()
        if self.parent_element:
            self.parent_element.publish()

    def delete(self, *args, **kwargs):
        pathway = self.pathway
        parent_element = self.parent_element
        ret = super(PathwayElement, self).delete(*args, **kwargs)
        pathway.publish()
        if parent_element:
           parent_element.publish()
        return ret

    @cachemodel.cached_method(auto_publish=True)
    def cached_children(self):
        return self.pathwayelement_set.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_badges(self):
        return self.pathwayelementbadge_set.all()

    @property
    def cached_pathway(self):
        return Pathway.cached.get(pk=self.pathway_id)

    @property
    def jsonld_id(self):
        return settings.HTTP_ORIGIN+reverse('pathway_element_detail', kwargs={
            'issuer_slug': self.cached_pathway.cached_issuer.slug,
            'pathway_slug': self.cached_pathway.slug,
            'element_slug': self.slug})

    def recipient_completion(self, recipient, badge_instances):
        pass

    def get_alignment_url(self):
        if self.alignment_url:
            return self.alignment_url
        return self.jsonld_id

    def _update_badges_from_completion_requirements(self):
        if self.completion_requirements and self.completion_requirements.get('badges'):
            _idx = {badge.pk: badge for badge in self.cached_badges()}
            order = 1
            for badge_id in self.completion_requirements.get('badges'):
                try:
                    r = resolve(badge_id.replace(settings.HTTP_ORIGIN, ''))
                except Resolver404:
                    raise ValidationError("Invalid badge id: {}".format(badge_id))
                badge_slug = r.kwargs.get('slug')
                try:
                    badgeclass = BadgeClass.cached.get(slug=badge_slug)
                except BadgeClass.DoesNotExist:
                    raise ValidationError("Invalid badge id: {}".format(badge_id))

                try:
                    pathway_badge = PathwayElementBadge.cached.get(element=self, badgeclass=badgeclass)
                    if pathway_badge.pk in _idx:
                        del _idx[pathway_badge.pk]
                except PathwayElementBadge.DoesNotExist:
                    pathway_badge = PathwayElementBadge(pathway=self.cached_pathway, element=self, badgeclass=badgeclass)
                pathway_badge.ordering = order
                order += 1
                pathway_badge.save()
            if len(_idx):
                for badge in _idx.values():
                    badge.delete()
            self.publish()


class PathwayElementBadge(cachemodel.CacheModel):
    pathway = models.ForeignKey('pathway.Pathway')
    element = models.ForeignKey('pathway.PathwayElement')
    badgeclass = models.ForeignKey('issuer.BadgeClass')
    ordering = models.IntegerField(default=99)

    class Meta:
        ordering = ('ordering',)

    def publish(self):
        super(PathwayElementBadge, self).publish()
        self.publish_by('element', 'badgeclass')
        self.element.publish()

    def delete(self, *args, **kwargs):
        element = self.element
        ret = super(PathwayElementBadge, self).delete(*args, **kwargs)
        self.publish_delete('element', 'badgeclass')
        element.publish()
        return ret

    @property
    def cached_element(self):
        return PathwayElement.cached.get(pk=self.element_id)

    @property
    def cached_badgeclass(self):
        return BadgeClass.cached.get(pk=self.badgeclass_id)
