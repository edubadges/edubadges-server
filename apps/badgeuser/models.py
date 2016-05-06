from itertools import chain
from allauth.account.models import EmailAddress
import cachemodel
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractUser
from hashlib import md5
from rest_framework.authtoken.models import Token

from issuer.models import Issuer


class CachedEmailAddress(EmailAddress, cachemodel.CacheModel):
    class Meta:
        proxy = True

    def publish(self):
        super(CachedEmailAddress, self).publish()
        self.publish_by('email')
        self.user.publish()

    def delete(self, *args, **kwargs):
        user = self.user
        self.publish_delete('email')
        self.publish_delete('pk')
        super(CachedEmailAddress, self).delete(*args, **kwargs)
        user.publish()

    def set_as_primary(self, conditional=False):
        # shadow parent function, but use CachedEmailAddress manager to ensure cache gets updated
        old_primary = CachedEmailAddress.objects.get_primary(self.user)
        if old_primary:
            if conditional:
                return False
            old_primary.primary = False
            old_primary.save()
        return super(CachedEmailAddress, self).set_as_primary(conditional=conditional)



class BadgeUser(AbstractUser, cachemodel.CacheModel):
    """
    A full-featured user model that can be an Earner, Issuer, or Consumer of Open Badges
    """

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('badge user')
        verbose_name_plural = _('badge users')
        db_table = 'users'

    def __unicode__(self):
        return self.email

    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'user_id': self.pk})

    def get_full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def publish(self):
        super(BadgeUser, self).publish()
        self.publish_by('username')

    def delete(self, *args, **kwargs):
        super(BadgeUser, self).delete(*args, **kwargs)
        self.publish_delete('username')

    @cachemodel.cached_method(auto_publish=True)
    def cached_emails(self):
        return EmailAddress.objects.filter(user=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return Issuer.objects.filter( Q(owner__id=self.id) | Q(staff__id=self.id) ).distinct()

    def cached_badgeclasses(self):
        return chain.from_iterable(issuer.cached_badgeclasses() for issuer in self.cached_issuers())

    @cachemodel.cached_method(auto_publish=True)
    def cached_token(self):
        user_token, created = \
                Token.objects.get_or_create(user=self)
        return user_token.key

    def replace_token(self):
        Token.objects.filter(user=self).delete()
        # user_token, created = \
        #         Token.objects.get_or_create(user=self)
        self.save()
        return self.cached_token()

    def save(self, *args, **kwargs):
        if not self.username:
            # md5 hash the email and then encode as base64 to take up only 25 characters
            hashed = md5(self.email).digest().encode('base64')[:-1]  # strip last character because its a newline
            self.username = "badgr{}".format(hashed[:25])

        if getattr(settings, 'BADGEUSER_SKIP_LAST_LOGIN_TIME', True):
            # skip saving last_login to the database
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None and 'last_login' in kwargs['update_fields']:
                kwargs['update_fields'].remove('last_login')
                if len(kwargs['update_fields']) < 1:
                    # nothing to do, abort so we dont call .publish()
                    return
        return super(BadgeUser, self).save(*args, **kwargs)
