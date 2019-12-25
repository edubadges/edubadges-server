import random

from django.contrib.auth import user_logged_out
from django.db import models
from django.utils import timezone
from entity.models import BaseEntity
from ims.models import LTITenant
from issuer.models import BadgeClass, Issuer


def get_uuid():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(25))


class LtiPayload(models.Model):
    date_created = models.DateTimeField(default=timezone.now)
    data = models.TextField()


class LtiBadgeUserTennant(models.Model):
    badge_user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    lti_tennant = models.ForeignKey(LTITenant, on_delete=models.CASCADE)
    lti_user_id = models.CharField(max_length=512)
    token = models.CharField(max_length=512, null=True)
    current_lti_data = models.TextField(null=True, blank=True)
    staff= models.BooleanField(default=False)
    expires = models.DateTimeField(null=True)


class BadgeClassLtiContext(models.Model):
    badge_class = models.ForeignKey(BadgeClass, on_delete=models.CASCADE, related_name='lti_context')
    context_id = models.CharField(max_length=512)

    class Meta:
        unique_together = ('badge_class', 'context_id',)


class UserCurrentContextId(models.Model):
    badge_user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    context_id = models.CharField(max_length=512, null=True)

    class Meta:
        unique_together = ('badge_user', 'context_id',)

#delete when user logs out
def delete_user_context_id(**kwargs):
    UserCurrentContextId.objects.filter(badge_user=kwargs['user']).all().delete()

user_logged_out.connect(delete_user_context_id)



class LtiClient(models.Model):
    date_created = models.DateTimeField(default=timezone.now)
    name = models.CharField(max_length=400, default='', blank=True, null=True)

    is_active = models.BooleanField(default=True)

    issuer = models.ForeignKey(Issuer, related_name='lti_client', on_delete=models.CASCADE)

    consumer_key = models.CharField(max_length=50, default=get_uuid)
    shared_secret = models.CharField(max_length=50, default=get_uuid)

    def __str__(self):
        return self.name

    @property
    def institution(self):
        if self.issuer:
            return self.issuer.institution
        return None

    def validate_unique(self, *args, **kwargs):
        super(LtiClient, self).validate_unique(*args, **kwargs)
        if self.__class__.objects.filter(issuer=self.issuer, name=self.name).exists():
            raise ValidationError(
                message='LtiClient with this name and Issuer already exists.',
                code='unique_together',
            )

    def save(self, *args, **kwargs):
        self.validate_unique()
        super(LtiClient, self).save(*args, **kwargs)


class ResourceLinkBadge(models.Model):
    # resource link is unique per placement, for each placement a unique badgeClass is created
    date_created = models.DateTimeField(default=timezone.now)

    resource_link = models.CharField(unique=True, max_length=255)
    issuer = models.ForeignKey(Issuer, related_name='lti_resource_link', on_delete=models.CASCADE)
    badge_class = models.ForeignKey(BadgeClass, related_name='lti_resource_link', on_delete=models.CASCADE)


class StudentsEnrolled(BaseEntity, models.Model):
    badge_class = models.ForeignKey(BadgeClass, related_name='lti_students', on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    date_consent_given = models.DateTimeField(default=None, blank=True, null=True)
    user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    badge_instance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE, null=True)
    date_awarded = models.DateTimeField(default=None, blank=True, null=True)
    denied = models.BooleanField(default=False)
    badge_class_lti_context = models.ForeignKey(BadgeClassLtiContext, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.email

    @property
    def assertion_slug(self):
        return self.badge_instance.entity_id

    @property
    def email(self):
        return self.user.primary_email

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    @property
    def edu_id(self):
        social_account = self.user.get_social_account()
        if social_account.provider == 'edu_id':
            return social_account.extra_data['sub']
        elif social_account.provider == 'surfconext_ala':
            return social_account.extra_data['sub']
        else:
            raise ValueError('User belonging to this enrollment has no eduid')
        
    def assertion_is_revoked(self):
        if self.badge_instance:
            return self.badge_instance.revoked
        else:
            return False    
