import cachemodel
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.models import AbstractUser


class BadgeUser(AbstractUser, cachemodel.CacheModel):
    """
    A full-featured user model that can be an Earner, Issuer, or Consumer of Open Badges
    """

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('badgeuser')
        verbose_name_plural = _('badgeusers')
        db_table = 'users'

    def __unicode__(self):
        return self.username

    def get_absolute_url(self):
        return "/user/%s/" % urlquote(self.username)

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def publish(self):
        super(BadgeUser, self).publish()
        self.publish_by('username')
