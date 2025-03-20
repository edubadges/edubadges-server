import random

from django.db import models
from django.utils import timezone

from entity.models import BaseVersionedEntity
from issuer.models import BadgeClass


def get_uuid():
    return ''.join(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(25))


class StudentsEnrolled(BaseVersionedEntity, models.Model):
    badge_class = models.ForeignKey(BadgeClass, related_name='lti_students', on_delete=models.CASCADE)
    date_created = models.DateTimeField(default=timezone.now)
    date_consent_given = models.DateTimeField(default=None, blank=True, null=True)
    user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    badge_instance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE, null=True)
    date_awarded = models.DateTimeField(default=None, blank=True, null=True)
    denied = models.BooleanField(default=False)
    deny_reason = models.TextField(blank=True, null=True, default=None)
    evidence_url = models.CharField(max_length=512, blank=True, null=True, default=None)
    narrative = models.TextField(blank=True, null=True, default=None)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        self.badge_class.remove_cached_data(['cached_enrollments', 'cached_pending_enrollments'])
        return super(StudentsEnrolled, self).save(*args, **kwargs)

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
            return social_account.extra_data['eduid']
        else:
            raise ValueError('User belonging to this enrollment has no eduid')

    def assertion_is_revoked(self):
        if self.badge_instance:
            return self.badge_instance.revoked
        else:
            return False

    def get_permissions(self, user):
        """
        Function that equates permission for this Enrollment to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badge_class.get_permissions(user)
