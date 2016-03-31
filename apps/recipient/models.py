# Created by wiggins@concentricsky.com on 3/31/16.
import basic_models
from autoslug import AutoSlugField
from django.db import models
import cachemodel


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
        self.recipient_group.publish()

    def delete(self, *args, **kwargs):
        group = self.recipient_group
        ret = super(RecipientGroupMembership, self).delete(*args, **kwargs)
        group.publish()
        return ret

    def populate_slug(self):
        return "{}-{}".format(self.recipient_group.slug, self.recipient_profile.slug)
