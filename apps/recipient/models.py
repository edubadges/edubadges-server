# Created by wiggins@concentricsky.com on 3/31/16.
import basic_models
from autoslug import AutoSlugField
from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse
import cachemodel

from issuer.models import BadgeInstance
from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.utils import OriginSetting
from pathway.completionspec import CompletionRequirementSpecFactory, ElementJunctionCompletionRequirementSpec
from pathway.models import Pathway

class RecipientProfile(basic_models.DefaultModel):
    slug = AutoSlugField(max_length=254, populate_from='recipient_identifier', unique=True, blank=False)
    badge_user = models.ForeignKey('badgeuser.BadgeUser', null=True, blank=True)
    recipient_identifier = models.EmailField(max_length=1024)
    public = models.BooleanField(default=False)
    display_name = models.CharField(max_length=254)

    cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='slug')

    def __unicode__(self):
        if self.display_name:
            return self.display_name
        return self.recipient_identifier

    def publish(self):
        super(RecipientProfile, self).publish()
        self.publish_by('slug')

    @property
    def jsonld_id(self):
        return u'mailto:{}'.format(self.recipient_identifier)

    def cached_completions(self, pathway):
        # get recipients instances that are aligned to this pathway
        badgeclasses = pathway.cached_badgeclasses()
        instances = filter(lambda i: not i.revoked and i.cached_badgeclass in badgeclasses, self.cached_badge_instances())

        # recurse the tree to build completions
        tree = pathway.element_tree
        completion_spec = CompletionRequirementSpecFactory.parse_element(tree['element'])

        if not completion_spec:
            # if there is no completionspec, infer one of elementjunction of all children elements
            completion_spec = ElementJunctionCompletionRequirementSpec(
                junction_type=CompletionRequirementSpecFactory.JUNCTION_TYPE_CONJUNCTION,
                required_number=len(tree['children']),
                elements=(c['element'].jsonld_id for c in tree['children'].itervalues()))
            tree['element'].completion_requirements = completion_spec.serialize()

        if completion_spec.completion_type == CompletionRequirementSpecFactory.BADGE_JUNCTION:
            return [completion_spec.check_completion(tree, instances)]
        elif completion_spec.completion_type == CompletionRequirementSpecFactory.ELEMENT_JUNCTION:
            return completion_spec.check_completions(tree, instances)
        else:
            # unsupported completion_type
            return []

    @cachemodel.cached_method(auto_publish=True)
    def cached_group_memberships(self):
        return RecipientGroupMembership.objects.filter(recipient_profile=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_badge_instances(self):
        return BadgeInstance.objects.filter(revoked=False, recipient_identifier=self.recipient_identifier)




class RecipientGroup(basic_models.DefaultModel):
    issuer = models.ForeignKey('issuer.Issuer')
    name = models.CharField(max_length=254)
    slug = AutoSlugField(max_length=254, populate_from='name', unique=True, blank=False)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField('RecipientProfile', through='recipient.RecipientGroupMembership')
    pathways = models.ManyToManyField('pathway.Pathway', related_name='recipient_groups')

    cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='group_slug')

    def __unicode__(self):
        return self.name

    def publish(self):
        super(RecipientGroup, self).publish()
        self.publish_by('slug')
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        issuer = self.issuer
        ret = super(RecipientGroup, self).delete(*args, **kwargs)
        issuer.publish()
        self.publish_delete('slug')
        return ret

    @cachemodel.cached_method(auto_publish=True)
    def cached_members(self):
        return RecipientGroupMembership.objects.filter(recipient_group=self)

    def member_count(self):
        return len(self.cached_members())

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathways(self):
        return self.pathways.filter(is_active=True)

    @property
    def jsonld_id(self):
        return OriginSetting.JSON+reverse(
            'recipient_group_detail',
            kwargs={'issuer_slug': self.issuer.slug, 'group_slug': self.slug}
        )


class RecipientGroupMembership(cachemodel.CacheModel):
    slug = AutoSlugField(max_length=254, unique=True, populate_from='populate_slug')
    recipient_profile = models.ForeignKey('recipient.RecipientProfile')
    recipient_group = models.ForeignKey('recipient.RecipientGroup')
    membership_name = models.CharField(max_length=254)

    @property
    def jsonld_id(self):
        return u"mailto:{}".format(self.recipient_identifier)

    @property
    def recipient_identifier(self):
        return self.recipient_profile.recipient_identifier

    def publish(self):
        super(RecipientGroupMembership, self).publish()
        self.publish_by('slug')
        self.recipient_group.publish()
        self.recipient_profile.publish()

    def delete(self, *args, **kwargs):
        group = self.recipient_group
        profile = self.recipient_profile
        ret = super(RecipientGroupMembership, self).delete(*args, **kwargs)
        group.publish()
        profile.publish()
        return ret

    def populate_slug(self):
        return "{}-{}".format(self.recipient_group.slug, self.recipient_profile.slug)

    @property
    def jsonld_id(self):
        return self.recipient_profile.jsonld_id