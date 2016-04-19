# Created by wiggins@concentricsky.com on 3/31/16.
import basic_models
from autoslug import AutoSlugField
from django.db import models
import cachemodel

from issuer.models import BadgeInstance
from pathway.completionspec import CompletionRequirementSpecFactory


class RecipientProfile(cachemodel.CacheModel):
    slug = AutoSlugField(max_length=254, populate_from='recipient_identifier', unique=True, blank=False)
    badge_user = models.ForeignKey('badgeuser.BadgeUser', null=True, blank=True)
    recipient_identifier = models.EmailField(max_length=1024)
    public = models.BooleanField(default=False)
    display_name = models.CharField(max_length=254)

    def __unicode__(self):
        if self.display_name:
            return self.display_name
        return self.recipient_identifier

    def publish(self):
        super(RecipientProfile, self).publish()
        self.publish_by('slug')

    @property
    def json_id(self):
        return u'mailto:{}'.format(self.recipient_identifier)

    # @cachemodel.cached_method(auto_publish=False)
    def cached_completions(self, pathway):
        # get recipients instances that are aligned to this pathway
        badgeclasses = pathway.cached_badgeclasses()
        instances = BadgeInstance.objects.filter(badgeclass__in=badgeclasses, recipient_identifier=self.recipient_identifier)

        # recurse the tree to build completions
        tree = pathway.build_element_tree()
        completions = []

        def _find_child_with_id(children, id):
            for child in children:
                if id == child['element'].json_id:
                    return child

        def _recurse(node):
            completion = {
                "element": node['element'].json_id,
                "completed": False,
                "completedRequirementCount": 0,
            }
            # recurse depth first
            if node['element'].completion_requirements:
                completion_spec = node['element'].completion_spec
                completion['completedRequirementCount'] = completion_spec.required_number
                if completion_spec.completion_type == CompletionRequirementSpecFactory.ELEMENT_JUNCTION:
                    for element_id in completion_spec.elements:
                        child = _find_child_with_id(node['children'], element_id)
                        _recurse(child)
                elif node.completion_spec.completion_type == CompletionRequirementSpecFactory.BADGE_JUNCTION:
                    completion.update(node.completion_spec.check_completion(instances))
            completions.append(completion)
        _recurse(tree)

        return completions


class RecipientGroup(basic_models.DefaultModel):
    issuer = models.ForeignKey('issuer.Issuer')
    name = models.CharField(max_length=254)
    slug = AutoSlugField(max_length=254, populate_from='name', unique=True, blank=False)
    description = models.TextField(blank=True, null=True)
    members = models.ManyToManyField('RecipientProfile', through='recipient.RecipientGroupMembership')

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


class RecipientGroupMembership(cachemodel.CacheModel):
    slug = AutoSlugField(max_length=254, unique=True, populate_from='populate_slug')
    recipient_profile = models.ForeignKey('recipient.RecipientProfile')
    recipient_group = models.ForeignKey('recipient.RecipientGroup')
    membership_name = models.CharField(max_length=254)

    def publish(self):
        super(RecipientGroupMembership, self).publish()
        self.publish_by('slug')
        self.recipient_group.publish()

    def delete(self, *args, **kwargs):
        group = self.recipient_group
        ret = super(RecipientGroupMembership, self).delete(*args, **kwargs)
        group.publish()
        return ret

    def populate_slug(self):
        return "{}-{}".format(self.recipient_group.slug, self.recipient_profile.slug)
