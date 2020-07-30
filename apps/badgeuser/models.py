import base64
import datetime
import re
from itertools import chain
from jsonfield import JSONField

import cachemodel
from allauth.account.models import EmailAddress, EmailConfirmation
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token
from rest_framework.authtoken.models import Token

from badgeuser.managers import CachedEmailAddressManager, BadgeUserManager, EmailAddressCacheModelManager
from entity.models import BaseVersionedEntity
from issuer.models import BadgeInstance
from lti_edu.models import StudentsEnrolled
from mainsite.exceptions import BadgrApiException400, BadgrValidationError
from mainsite.models import ApplicationInfo, EmailBlacklist, BaseAuditedModel, BadgrApp
from mainsite.utils import open_mail_in_browser
from signing.models import AssertionTimeStamp
from badgeuser.utils import generate_badgr_username
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class UserProvisionment(BaseAuditedModel, BaseVersionedEntity, cachemodel.CacheModel):
    user = models.ForeignKey('badgeuser.BadgeUser', null=True, on_delete=models.CASCADE)
    email = models.EmailField()
    content_type = models.ForeignKey(ContentType, null=True, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True)  # id of the related object the invitation was for
    entity = GenericForeignKey('content_type', 'object_id')
    data = JSONField(null=True)
    for_teacher = models.BooleanField()
    rejected = models.BooleanField(default=False)
    TYPE_INVITATION = 'Invitation'  # invitation to the application
    TYPE_FIRST_ADMIN_INVITATION = 'FirstAdminInvitation'  # invitation to the application
    TYPE_CHOICES = (
        (TYPE_INVITATION, 'Invitation'),
        (TYPE_FIRST_ADMIN_INVITATION, 'FirstAdminInvitation'),
    )
    type = models.CharField(max_length=254, choices=TYPE_CHOICES)
    notes = models.TextField(blank=True, null=True, default=None)

    def _validate_unique(self, exclude=None):
        """Custom uniqueness validation of the provisionment, used before save"""
        if UserProvisionment.objects.filter(
                type=self.type,
                rejected=False,
                for_teacher=self.for_teacher,
                email=self.email).exclude(pk=self.pk).exists():
            raise BadgrValidationError('There may be only one invite per email address.', 501)
        return super(UserProvisionment, self).validate_unique(exclude=exclude)

    def _validate_staff_collision(self):
        """validate to see if there is a existing staff membership that conflicts for the entity of this invite"""
        if self.user and self.entity.get_all_staff_memberships_in_current_branch(self.user):
            raise BadgrValidationError('Cannot invite user for this entity. There is a conflicting staff membership.', 502)

    def _validate_invite_collision(self):
        """validate to see if the there is another invite that collides with this one
         (i.e. if both are created the staff memberships will collide"""
        all_entities_in_same_branch = self.entity.get_all_entities_in_branch()
        all_invites_for_same_user = UserProvisionment.objects.filter(email=self.email)
        for invite in all_invites_for_same_user:
            if invite != self and invite.entity in all_entities_in_same_branch:
                raise BadgrValidationError('Cannot invite user for this entity. There is a conflicting invite.', 503)

    def get_permissions(self, user):
        return self.entity.get_permissions(user)

    def match_user(self, user):
        '''Sets given user as the matched user'''
        try:
            entity_institution = self.entity.institution
        except AttributeError:
            entity_institution = self.entity
        if user.institution != entity_institution:
            raise BadgrValidationError('May not invite user from other institution', 504)
        if user.is_teacher and not self.for_teacher:
            raise BadgrValidationError('This invite is for a student', 505)
        if not user.is_teacher and self.for_teacher:
            raise BadgrValidationError('This invite is for a teacher', 506)
        self.user = user
        self.save()

    def find_and_match_user(self):
        """Finds a user with the same emailadress and sets it as the matched user"""
        try:
            user = BadgeUser.objects.get(email=self.email, is_teacher=self.for_teacher)
            self.match_user(user)
        except BadgeUser.DoesNotExist:
            pass


    def add_entity(self, entity):
        self.content_type = ContentType.objects.get_for_model(entity)
        self.object_id = entity.pk
        self.save()

    # @property
    # def acceptance_link(self):
    #     return OriginSetting.HTTP + reverse('user_provision_accept', kwargs={'entity_id': self.entity_id})

    def send_email(self):
        """Send the invitation email to the recipient"""
        try:
            EmailBlacklist.objects.get(email=self.email)
        except EmailBlacklist.DoesNotExist:
            subject = 'You have been invited'
            login_link = BadgrApp.objects.get(pk=1).email_confirmation_redirect
            if self.user:
                message = "You have been invited for a staff membership. Please login to accept. \n {}".format(login_link)
            if not self.user:
                message = "You have been invited to the EduBadges Issuer Platform. Please signup to accept. \n {}".format(login_link)
                send_mail(subject, message, None, [self.email])

    def perform_provisioning(self):
        '''Actually create the objects that form the provisionment'''
        permissions = self.data
        prov = self.entity.create_staff_membership(self.user, permissions)
        self.delete()
        return prov

    def accept(self):
        """Accept the provsionment"""
        return self.perform_provisioning()

    def reject(self):
        """reject the provisionment"""
        self.rejected = True
        self.save()

    def _run_validations(self):
        if self.type == UserProvisionment.TYPE_FIRST_ADMIN_INVITATION:
            self._validate_unique()
        else:
            self._validate_staff_collision()
            self._validate_invite_collision()

    def _remove_cache(self):
        if self.entity:
            self.entity.remove_cached_data(['cached_userprovisionments'])

    def save(self, *args, **kwargs):
        self._run_validations()
        self._remove_cache()
        return super(UserProvisionment, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._remove_cache()
        return super(UserProvisionment, self).delete(*args, **kwargs)


class CachedEmailAddress(EmailAddress, cachemodel.CacheModel):
    objects = CachedEmailAddressManager()
    cached = EmailAddressCacheModelManager()

    class Meta:
        proxy = True
        verbose_name = _("email address")
        verbose_name_plural = _("email addresses")

    def generate_forgot_password_time_cache_key(self):
        return "{}_forgot_request_date".format(self.email)

    def get_last_forgot_password_sent_time(self):
        cached_time = cache.get(self.generate_forgot_password_time_cache_key())
        return cached_time

    def set_last_forgot_password_sent_time(self, new_datetime):
        cache.set(self.generate_forgot_password_time_cache_key(), new_datetime)

    def generate_verification_time_cache_key(self):
        return "{}_verification_request_date".format(self.email)

    def get_last_verification_sent_time(self):
        cached_time = cache.get(self.generate_verification_time_cache_key())
        return cached_time

    def set_last_verification_sent_time(self, new_datetime):
        cache.set(self.generate_verification_time_cache_key(), new_datetime)

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

    def save(self, *args, **kwargs):
        super(CachedEmailAddress, self).save(*args, **kwargs)

        if not self.emailaddressvariant_set.exists() and self.email != self.email.lower():
            self.add_variant(self.email.lower())

#     @cachemodel.cached_method(auto_publish=True) # no caching due to errors in update_user_params
    def cached_variants(self):
        return self.emailaddressvariant_set.all()

    def add_variant(self, email_variation):
        existing_variants = EmailAddressVariant.objects.filter(
            canonical_email=self, email=email_variation
        )
        if email_variation not in [e.email for e in existing_variants.all()]:
            return EmailAddressVariant.objects.create(
                canonical_email=self, email=email_variation
            )
        else:
            raise ValidationError("Email variant {} already exists".format(email_variation))


class ProxyEmailConfirmation(EmailConfirmation):
    class Meta:
        proxy = True
        verbose_name = _("email confirmation")
        verbose_name_plural = _("email confirmations")


class EmailAddressVariant(models.Model):
    email = models.EmailField(blank=False)
    canonical_email = models.ForeignKey(CachedEmailAddress, on_delete=models.CASCADE, blank=False)

    def save(self, *args, **kwargs):
        self.is_valid(raise_exception=True)

        super(EmailAddressVariant, self).save(*args, **kwargs)
        self.canonical_email.save()

    def __unicode__(self):
        return self.email

    @property
    def verified(self):
        return self.canonical_email.verified

    def is_valid(self, raise_exception=False):
        def fail(message):
            if raise_exception:
                raise ValidationError(message)
            else:
                self.error = message
                return False

        if not self.canonical_email_id:
            try:
                self.canonical_email = CachedEmailAddress.cached.get(email=self.email)
            except CachedEmailAddress.DoesNotExist:
                fail("Canonical Email Address not found")

        if not self.canonical_email.email.lower() == self.email.lower():
            fail("New EmailAddressVariant does not match stored email address.")

        return True


class UserCachedObjectGetterMixin(object):
    """
    Base class to group all cached object-getter functionality of user, purely for readability
    """
    def _get_objects_with_permissions(self, permissions, type=None):
        """
        :param permission: list of strings representing permissions
        :param type: string that represent class.__name__ ('Institution', 'Faculty', 'Issuer', 'BadgeClass' or None)
        :return: list of objects for which this user has the given permissions for.
        """
        permissioned_objects = []

        def object_tree_walker(obj, permissions, looking_for=type, override_permissions=False):
            """
            Recursively walks the object tree to find objects of which the user has all the given permissions for.
            """
            if obj.check_local_permissions(self, permissions) or override_permissions:
                if looking_for:
                    if obj.__class__.__name__ == looking_for:
                        permissioned_objects.append(obj)
                else:
                    permissioned_objects.append(obj)
                override_permissions = True
            try:
                for child in obj.children:
                    object_tree_walker(child, permissions, looking_for, override_permissions)
            except AttributeError:  # no more kids
                pass
        if not self.is_teacher:
            raise ValueError('User must be teacher to walk the permission tree')
        tree_root = self.institution
        object_tree_walker(tree_root, permissions)
        return permissioned_objects

    def get_all_objects_with_permissions(self, permissions):
        return self._get_objects_with_permissions(permissions)

    def get_all_badgeclasses_with_permissions(self, permissions):
        return self._get_objects_with_permissions(permissions, 'BadgeClass')

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return BadgeInstance.objects.filter(user=self)

    @cachemodel.cached_method()
    def cached_pending_enrollments(self):
        return StudentsEnrolled.objects.filter(user=self, badge_instance=None)

    # @cachemodel.cached_method(auto_publish=True)
    # turned it off, because if user logs in for FIRST time, this caching will result in the user having no verified emails.
    # This results in api calls responding with a 403 after the failure of the AuthenticatedWithVerifiedEmail permission check.
    # Which will logout the user automatically with the error: Token expired.
    def cached_emails(self):
        return CachedEmailAddress.objects.filter(user=self)

    def cached_email_variants(self):
        return chain.from_iterable(email.cached_variants() for email in self.cached_emails())

    @cachemodel.cached_method(auto_publish=True)
    def cached_token(self):
        user_token, created = \
                Token.objects.get_or_create(user=self)
        return user_token.key

    @cachemodel.cached_method(auto_publish=True)
    def cached_terms_agreements(self):
        return list(self.termsagreement_set.all())

    @cachemodel.cached_method(auto_publish=True)
    def cached_institution_staff(self):
        try:
            return InstitutionStaff.objects.get(user=self)
        except InstitutionStaff.DoesNotExist:
            return None

    @cachemodel.cached_method(auto_publish=True)
    def cached_faculty_staffs(self):
        return list(FacultyStaff.objects.filter(user=self))

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuer_staffs(self):
        return list(IssuerStaff.objects.filter(user=self))

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclass_staffs(self):
        return list(BadgeClassStaff.objects.filter(user=self))

    @cachemodel.cached_method()
    def cached_colleagues(self):
        return list(BadgeUser.objects.filter(institution=self.institution))


class UserPermissionsMixin(object):
    """
    Base class to group all permission functionality of user, purely for readability
    """
    def is_user_within_scope(self, user):
        """
        See if user has other user in his scope, (i.e. is other user found in your institution)
        This is used when creating a new staff membership object, then this user must be in your scope.
        """
        if self == user:
            return False  # cannot administrate yourself
        return self.institution == user.institution

    def is_staff_membership_within_scope(self, staff_membership):
        """
        See if staff membership is in this user's scope. This is used when editing or removing staff membership objects.
        """
        if self == staff_membership.user:
            return False  # cannot administrate yourself
        all_administrable_objects = self.get_all_objects_with_permissions(['may_administrate_users'])
        for obj in all_administrable_objects:
            for staff in obj.staff_items:
                if staff == staff_membership:
                    return True  # staff membership is administrable
        return False

    def get_permissions(self, obj):
        """
        Convenience method to get permissions for this user & object combination
        :param obj: Instance of Institution, Faculty, Issuer or Badgeclass
        :return: dictionary
        """
        return obj.get_permissions(self)

    @property
    def may_sign_assertion(self, badgeinstance):
        """
        Method to check if user may sign the assertion
        """
        perms = badgeinstance.badgeclass.get_permissions(self)
        return perms['may_sign']

    def may_enroll(self, badge_class, raise_exception=False):
        """
        Checks to see if user may enroll
            no enrollments: May enroll
            any not awarded assertions: May not enroll
            Any awarded and not revoked: May not enroll
            All revoked: May enroll
        """
        social_account = self.get_social_account()
        if social_account.provider == 'edu_id':
            enrollments = StudentsEnrolled.objects.filter(user=social_account.user, badge_class_id=badge_class.pk)
            if not enrollments:
                return True  # no enrollments
            else:
                for enrollment in enrollments:
                    if not bool(enrollment.badge_instance):  # has never been awarded
                        if raise_exception:
                            raise BadgrApiException400('May not enroll: already enrolled', 201)
                        return False
                    else:  # has been awarded
                        if not enrollment.assertion_is_revoked():
                            if raise_exception:
                                raise BadgrApiException400('May not enroll: you already have been awarded this badge', 202)
                            return False
                return True  # all have been awarded and revoked
        else:  # no eduID
            if raise_exception:
                raise BadgrApiException400("May not enroll: you don't have a student account", 203)
            return False


class BadgeUser(UserCachedObjectGetterMixin, UserPermissionsMixin, AbstractUser, BaseVersionedEntity):
    """
    A full-featured user model that can be an Earner, Issuer, or Consumer of Open Badges
    """
    entity_class_name = 'BadgeUser'
    is_teacher = models.BooleanField(default=False)
    invited = models.BooleanField(default=False)

    badgrapp = models.ForeignKey('mainsite.BadgrApp', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    is_staff = models.BooleanField(
        _('Backend-staff member'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )

    # canvas LTI id
    lti_id = models.CharField(unique=True, max_length=50, default=None, null=True, blank=True,
                              help_text='LTI user id, unique per user')
    marketing_opt_in = models.BooleanField(default=False)

    objects = BadgeUserManager()

    institution = models.ForeignKey('institution.Institution', on_delete=models.CASCADE, null=True)

    class Meta:
        verbose_name = _('badge user')
        verbose_name_plural = _('badge users')
        db_table = 'users'
        permissions=(('view_issuer_tab', 'User can view Issuer tab in front end'),
                     ('view_management_tab', 'User can view Management dashboard'),
                     ('has_faculty_scope', 'User has faculty scope'),
                     ('has_institution_scope', 'User has institution scope'),
                     ('ui_issuer_add', 'User can add issuer in front end'),
                     )

    def __unicode__(self):
        return "{} <{}>".format(self.get_full_name(), self.email)

    @property
    def email_items(self):
        return self.cached_emails()

    @email_items.setter
    def email_items(self, value):
        """
        Update this users EmailAddress from a list of BadgeUserEmailSerializerV2 data
        :param value: list(BadgeUserEmailSerializerV2)
        :return: None
        """
        if len(value) < 1:
            raise ValidationError("Must have at least 1 email")

        new_email_idx = {d['email']: d for d in value}

        primary_count = sum(1 if d.get('primary', False) else 0 for d in value)
        if primary_count != 1:
            raise ValidationError("Must have exactly 1 primary email")

        with transaction.atomic():
            # add or update existing items
            for email_data in value:
                primary = email_data.get('primary', False)
                emailaddress, created = CachedEmailAddress.cached.get_or_create(
                    email=email_data['email'],
                    defaults={
                        'user': self,
                        'primary': primary
                    })
                if created:
                    # new email address send a confirmation
                    emailaddress.send_confirmation()
                else:
                    if emailaddress.user_id == self.id:
                        # existing email address owned by user
                        emailaddress.primary = primary
                        emailaddress.save()
                    elif not emailaddress.verified:
                        # existing unverified email address, handover to this user
                        emailaddress.user = self
                        emailaddress.primary = primary
                        emailaddress.save()
                        emailaddress.send_confirmation()
                    else:
                        # existing email address used by someone else
                        raise ValidationError("Email '{}' may already be in use".format(email_data.get('email')))

            # remove old items
            for emailaddress in self.email_items:
                if emailaddress.email not in new_email_idx:
                    emailaddress.delete()

    @property
    def current_symmetric_key(self):
        return self.symmetrickey_set.get(current=True)

    def accept_terms(self, terms):
        agreement, _ = TermsAgreement.objects.get_or_create(user=self, terms=terms)
        agreement.agreed_version = terms.version
        agreement.save()

    def accept_general_terms(self):
        general_terms = Terms.get_general_terms(self)
        for terms in general_terms:
            self.accept_terms(terms)
        self.remove_cached_data(['cached_terms_agreements'])

    def general_terms_accepted(self):
        nr_accepted = 0
        general_terms = Terms.get_general_terms(self)
        for general_term in general_terms:
            if general_term.has_been_accepted_by(self):
                nr_accepted += 1
        return general_terms.__len__() == nr_accepted

    def get_full_name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        else:
            return ''

    def match_provisionments(self):
        """Used to match provisions on initial login"""
        provisions = UserProvisionment.objects.filter(email=self.email, for_teacher=self.is_teacher)
        for provision in provisions:
            provision.match_user(self)
        return provisions

    def email_user(self, subject, message, from_email=None, attachments=None, **kwargs):
        """
        Sends an email to this User.
        """
        try:
            EmailBlacklist.objects.get(email=self.primary_email)
        except EmailBlacklist.DoesNotExist:
            # Allow sending, as this email is not blacklisted.
            if not attachments:
                if settings.LOCAL_DEVELOPMENT_MODE:
                    open_mail_in_browser(message)
                else:
                    send_mail(subject, message, from_email, [self.primary_email], **kwargs)
            else:
                from django.core.mail import EmailMessage
                if settings.LOCAL_DEVELOPMENT_MODE:
                    open_mail_in_browser(message)
                else:
                    email = EmailMessage(subject=subject,
                                         body=message,
                                         from_email=from_email,
                                         to=[self.primary_email],
                                         attachments=attachments)
                    email.send()
        else:
            return
            # TODO: Report email non-delivery somewhere.

    def publish(self):
        super(BadgeUser, self).publish()
        self.publish_by('username')

    def delete(self, *args, **kwargs):
        super(BadgeUser, self).delete(*args, **kwargs)
        self.publish_delete('username')

    def can_add_variant(self, email):
        try:
            canonical_email = CachedEmailAddress.objects.get(email=email, user=self, verified=True)
        except CachedEmailAddress.DoesNotExist:
            return False

        if email != canonical_email.email \
                and email not in [e.email for e in canonical_email.cached_variants()] \
                and EmailAddressVariant(email=email, canonical_email=canonical_email).is_valid():
            return True
        return False

    @property
    def primary_email(self):
        primaries = [e for e in self.cached_emails() if e.primary]
        if len(primaries) > 0:
            return primaries[0].email
        return self.email

    @property
    def verified_emails(self):
        return [e for e in self.cached_emails() if e.verified]

    @property
    def verified(self):
        if self.is_superuser:
            return True

        if len(self.verified_emails) > 0:
            return True

        return False

    @property
    def all_recipient_identifiers(self):
        return [self.get_recipient_identifier()]

    def get_eduperson_scoped_affiliations(self):
        social_account = self.get_social_account()
        return social_account.extra_data['eduperson_scoped_affiliation']

    def get_all_associated_institutions_identifiers(self):
        '''returns self.institution and all institutions in the social account '''
        if self.is_teacher:
            return [self.institution.identifier]
        else:
            return [affiliation.replace('affiliate@', '') for affiliation in self.get_eduperson_scoped_affiliations()]

    def get_recipient_identifier(self):
        from allauth.socialaccount.models import SocialAccount
        try:
            account = SocialAccount.objects.get(user=self.pk)
            return account.uid
        except SocialAccount.DoesNotExist:
            return None

    def get_social_account(self):
        from allauth.socialaccount.models import SocialAccount
        try:
            account = SocialAccount.objects.get(user=self.pk)
            return account
        except SocialAccount.DoesNotExist:
            return None

    @property
    def is_student(self):
        return not self.is_teacher

    def get_assertions_ready_for_signing(self):
        assertion_timestamps = AssertionTimeStamp.objects.filter(signer=self).exclude(proof='')
        return [ts.badge_instance for ts in assertion_timestamps if ts.badge_instance.signature == None]

    def replace_token(self):
        Token.objects.filter(user=self).delete()
        # user_token, created = \
        #         Token.objects.get_or_create(user=self)
        self.save()
        return self.cached_token()

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = generate_badgr_username(self.email)

        if getattr(settings, 'BADGEUSER_SKIP_LAST_LOGIN_TIME', True):
            # skip saving last_login to the database
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None and 'last_login' in kwargs['update_fields']:
                kwargs['update_fields'].remove('last_login')
                if len(kwargs['update_fields']) < 1:
                    # nothing to do, abort so we dont call .publish()
                    return
        return super(BadgeUser, self).save(*args, **kwargs)


class BadgrAccessTokenManager(models.Manager):

    def generate_new_token_for_user(self, user, scope='r:profile', application=None, expires=None, refresh_token=False):
        with transaction.atomic():
            if application is None:
                application, created = Application.objects.get_or_create(
                    client_id='public',
                    client_type=Application.CLIENT_PUBLIC,
                    authorization_grant_type=Application.GRANT_PASSWORD,
                )
                if created:
                    ApplicationInfo.objects.create(application=application)

            if expires is None:
                access_token_expires_seconds = getattr(settings, 'OAUTH2_PROVIDER', {}).get('ACCESS_TOKEN_EXPIRE_SECONDS', 86400)
                expires = timezone.now() + datetime.timedelta(seconds=access_token_expires_seconds)

            accesstoken = self.create(
                application=application,
                user=user,
                expires=expires,
                token=generate_token(),
                scope=scope
            )

        return accesstoken

    def get_from_entity_id(self, entity_id):
        # lookup by a faked
        padding = len(entity_id) % 4
        if padding > 0:
            entity_id = '{}{}'.format(entity_id, (4-padding)*'=')
        decoded = base64.urlsafe_b64decode(entity_id.encode('utf-8'))
        id = re.sub(r'^{}'.format(self.model.fake_entity_id_prefix), '', decoded)
        try:
            pk = int(id)
        except ValueError as e:
            pass
        else:
            try:
                obj = self.get(pk=pk)
            except self.model.DoesNotExist:
                pass
            else:
                return obj
        raise self.model.DoesNotExist


class BadgrAccessToken(AccessToken, cachemodel.CacheModel):
    objects = BadgrAccessTokenManager()
    fake_entity_id_prefix = "BadgrAccessToken.id="

    class Meta:
        proxy = True

    @property
    def entity_id(self):
        # fake an entityId for this non-entity
        digest = "{}{}".format(self.fake_entity_id_prefix, self.pk)
        b64_string = base64.urlsafe_b64encode(digest)
        b64_trimmed = re.sub(r'=+$', '', b64_string)
        return b64_trimmed

    def get_entity_class_name(self):
        return 'AccessToken'

    @property
    def application_name(self):
        return self.application.name

    @property
    def applicationinfo(self):
        try:
            return self.application.applicationinfo
        except ApplicationInfo.DoesNotExist:
            return ApplicationInfo()


class TermsUrl(cachemodel.CacheModel):
    terms = models.ForeignKey('badgeuser.Terms', on_delete=models.CASCADE)
    url = models.URLField(max_length=200, null=True)
    LANGUAGE_ENGLISH = 'english'
    LANGUAGE_DUTCH = 'dutch'
    LANGUAGE_CHOICES = (
        (LANGUAGE_ENGLISH, 'english'),
        (LANGUAGE_DUTCH, 'dutch')
    )
    language = models.CharField(max_length=255, choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH, blank=False, null=False)


class Terms(BaseAuditedModel, BaseVersionedEntity, cachemodel.CacheModel):
    version = models.PositiveIntegerField(default=1)
    institution = models.ForeignKey('institution.Institution', on_delete=models.CASCADE, related_name='terms', null=True, blank=True)

    TYPE_FORMAL_BADGE = 'formal_badge'
    TYPE_INFORMAL_BADGE = 'informal_badge'
    TYPE_SERVICE_AGREEMENT_STUDENT = 'service_agreement_student'
    TYPE_SERVICE_AGREEMENT_EMPLOYEE = 'service_agreement_employee'
    # TYPE_GENERAL_PRIVACY_STATEMENT = 'general_privacy_statement'
    TYPE_TERMS_OF_SERVICE = 'terms_of_service'
    TYPE_CHOICES = (
        (TYPE_FORMAL_BADGE, 'formal_badge'),
        (TYPE_INFORMAL_BADGE, 'informal_badge'),
        # (TYPE_GENERAL_PRIVACY_STATEMENT, 'general_privacy_statement'),
        (TYPE_SERVICE_AGREEMENT_STUDENT, 'service_agreement_student'),
        (TYPE_SERVICE_AGREEMENT_EMPLOYEE, 'service_agreement_employee'),
        (TYPE_TERMS_OF_SERVICE, 'terms_of_service')
    )
    terms_type = models.CharField(max_length=254, choices=TYPE_CHOICES, default=TYPE_TERMS_OF_SERVICE)

    @classmethod
    def get_general_terms(cls, user):
        if user.is_student:
            return list(Terms.objects.filter(terms_type__in=(Terms.TYPE_SERVICE_AGREEMENT_STUDENT,
                                                             Terms.TYPE_TERMS_OF_SERVICE)))
        elif user.is_teacher:
            return list(Terms.objects.filter(terms_type__in=(Terms.TYPE_SERVICE_AGREEMENT_EMPLOYEE,
                                                             Terms.TYPE_TERMS_OF_SERVICE)))
        raise BadgrValidationError('Cannot get general terms user is neither teacher nor student', 0)

    def has_been_accepted_by(self, user):
        for agreement in user.cached_terms_agreements():
            if agreement.terms == self:
                return self.version == agreement.agreed_version
        return False

    def accept(self, user):
        ''' make user accept terms
            returns: TermsAgreement'''
        # must work for updating increment and for accepting the first time
        terms_agreement, created = TermsAgreement.objects.get_or_create(user=user, terms=self)
        terms_agreement.agreed_version = self.version
        terms_agreement.save()
        user.remove_cached_data(['cached_terms_agreements'])
        return terms_agreement
                

class TermsAgreement(cachemodel.CacheModel):
    user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    terms = models.ForeignKey('badgeuser.Terms', on_delete=models.CASCADE)
    agreed = models.BooleanField(default=True)
    agreed_version = models.PositiveIntegerField(null=True)
    LANGUAGE_ENGLISH = 'english'
    LANGUAGE_DUTCH = 'dutch'
    LANGUAGE_CHOICES = (
        (LANGUAGE_ENGLISH, 'english'),
        (LANGUAGE_DUTCH, 'dutch')
    )
    agreed_language = models.CharField(max_length=255, choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH, blank=False, null=False)
