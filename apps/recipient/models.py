# Created by wiggins@concentricsky.com on 3/31/16.
import basic_models
import cachemodel
from django.core.urlresolvers import reverse
from django.db import models, transaction

from entity.models import BaseVersionedEntity
from issuer.models import BadgeInstance, BaseAuditedModel, Issuer
from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.utils import OriginSetting
from pathway.completionspec import CompletionRequirementSpecFactory, ElementJunctionCompletionRequirementSpec


class RecipientProfile(BaseVersionedEntity, basic_models.DefaultModel):
    badge_user = models.ForeignKey('badgeuser.BadgeUser', null=True, blank=True)
    recipient_identifier = models.EmailField(max_length=1024)
    public = models.BooleanField(default=False)
    display_name = models.CharField(max_length=254)

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=254, blank=True, null=True, default=None)

    cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='entity_id')

    def __unicode__(self):
        if self.display_name:
            return self.display_name
        return self.recipient_identifier

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


class RecipientGroup(BaseAuditedModel, BaseVersionedEntity, basic_models.ActiveModel):
    issuer = models.ForeignKey('issuer.Issuer')
    name = models.CharField(max_length=254)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField('RecipientProfile', through='recipient.RecipientGroupMembership')
    pathways = models.ManyToManyField('pathway.Pathway', related_name='recipient_groups')

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=254, blank=True, null=True, default=None)

    cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='group_slug')

    def __unicode__(self):
        return self.name

    def publish(self):
        super(RecipientGroup, self).publish()
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        ret = super(RecipientGroup, self).delete(*args, **kwargs)
        self.issuer.publish()
        return ret

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @cachemodel.cached_method(auto_publish=True)
    def cached_members(self):
        return RecipientGroupMembership.objects.filter(recipient_group=self)

    @property
    def membership_items(self):
        return self.cached_members()

    @membership_items.setter
    def membership_items(self, value):
        """
        Update this groups RecipientGroupMembmership from a list of RecipientGroupMembershipSerializerV2 data
        """
        existing_members_idx = {s.recipient_identifier: s for s in self.membership_items}
        new_members_idx = {s['recipient']['identifier']: s for s in value}

        with transaction.atomic():
            # add missing memberships
            for membership_data in value:
                recipient_identifer = membership_data['recipient']['identifier']
                if recipient_identifer not in existing_members_idx:
                    profile, profile_created = RecipientProfile.cached.get_or_create(
                        recipient_identifier=recipient_identifer
                    )
                    membership, created = RecipientGroupMembership.cached.get_or_create(
                        recipient_group=self,
                        recipient_profile=profile,
                        defaults={
                            'membership_name': membership_data['name']
                        }
                    )
                    if not created:
                        membership.membershi_name = membership_data['name']
                        membership.save()

            # remove old memberships
            for membership in self.membership_items:
                if membership.recipient_identifier not in new_members_idx:
                    membership.delete()

    def member_count(self):
        return len(self.cached_members())

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathways(self):
        return self.pathways.filter(is_active=True)

    @property
    def jsonld_id(self):
        return OriginSetting.HTTP+reverse('v2_api_recipient_group_detail', kwargs={
            'entity_id': self.entity_id
        })


class RecipientGroupMembership(BaseVersionedEntity):
    recipient_profile = models.ForeignKey('recipient.RecipientProfile')
    recipient_group = models.ForeignKey('recipient.RecipientGroup')
    membership_name = models.CharField(max_length=254)

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=254, blank=True, null=True, default=None)

    @property
    def jsonld_id(self):
        return u"mailto:{}".format(self.recipient_identifier)

    @property
    def cached_recipient_profile(self):
        return RecipientProfile.cached.get(id=self.recipient_profile_id)

    @property
    def cached_recipient_group(self):
        return RecipientGroup.cached.get(id=self.recipient_group_id)

    @property
    def recipient_identifier(self):
        return self.cached_recipient_profile.recipient_identifier

    def publish(self):
        super(RecipientGroupMembership, self).publish()
        self.recipient_group.publish()
        self.recipient_profile.publish()

    def delete(self, *args, **kwargs):
        ret = super(RecipientGroupMembership, self).delete(*args, **kwargs)
        self.recipient_group.publish()
        self.recipient_profile.publish()
        return ret

    def populate_slug(self):
        return "{}-{}".format(self.recipient_group.slug, self.recipient_profile.slug)

    @property
    def jsonld_id(self):
        return self.recipient_profile.jsonld_id