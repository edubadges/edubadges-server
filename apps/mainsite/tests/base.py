# encoding: utf-8


import os
import random
import time
import uuid
import string
from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APITransactionTestCase

from allauth.socialaccount.models import SocialAccount
from badgeuser.models import BadgeUser, TermsVersion
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.test import override_settings, TransactionTestCase
from django.utils import timezone
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite import TOP_DIR
from mainsite.models import BadgrApp, ApplicationInfo
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


def name_randomiser(name):
    s = ''.join(random.choices(string.ascii_lowercase, k=10))
    return name + '_' + s

class SetupOAuth2ApplicationHelper(object):
    def setup_oauth2_application(self,
                                 client_id=None,
                                 client_secret=None,
                                 name='test client app',
                                 allowed_scopes=None,
                                 trust_email=False,
                                 **kwargs):
        if client_id is None:
            client_id = "test"
        if client_secret is None:
            client_secret = "secret"

        if 'authorization_grant_type' not in kwargs:
            kwargs['authorization_grant_type'] = Application.GRANT_CLIENT_CREDENTIALS

        application = Application.objects.create(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            **kwargs
        )

        if allowed_scopes:
            application_info = ApplicationInfo.objects.create(
                application=application,
                name=name,
                allowed_scopes=allowed_scopes,
                trust_email_verification=trust_email
            )

        return application


class SetupHelper(object):

    def _add_eduid_socialaccount(self, user):
        random_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:{}c14-b952-4d7e-85fd-{}ac5c6f18".format(random.randint(1, 99999), random.randint(1, 9999))
        extra_data = {"family_name": user.last_name,
                      "sub": random_eduid,
                      "email": user.email,
                      "name": user.get_full_name(),
                      "given_name": user.first_name}
        socialaccount = SocialAccount(extra_data=extra_data,
                                      uid=random_eduid,
                                      provider='edu_id',
                                      user=user)
        socialaccount.save()

    def _add_surfconext_socialaccount(self, user):
        random_surfconext_id = str(uuid.uuid4())
        extra_data = {"family_name": user.last_name,
                      "sub": random_surfconext_id,
                      "email": user.email,
                      "name": user.get_full_name(),
                      "given_name": user.first_name}
        socialaccount = SocialAccount(extra_data=extra_data,
                                      uid=random_surfconext_id,
                                      provider='surf_conext',
                                      user=user)
        socialaccount.save()

    def _user_accept_terms(self, user):
        terms, created = TermsVersion.objects.get_or_create(version=1)
        user.agreed_terms_version = terms.version
        user.save()

    def _make_email_primary(self, user):
        email = user.cached_emails()[0]
        email.verified = True
        email.primary = True
        email.save()

    def _setup_user(self, first_name='firsty', last_name='lastington', authenticate=False, institution=None):
        email = 'setup_user_{}@email.test'.format(random.random())
        if not institution:
            institution = self.setup_institution()
        user = BadgeUser.objects.create(email=email,
                                        first_name=first_name,
                                        last_name=last_name)
        user.institution = institution
        user.save()
        self._user_accept_terms(user)
        self._make_email_primary(user)
        if authenticate:
            self.client.force_authenticate(user=user)
        return user

    def setup_teacher(self, first_name='', last_name='', authenticate=False, institution=None):
        user = self._setup_user(first_name, last_name, authenticate, institution=institution)
        self._add_surfconext_socialaccount(user)
        return user

    def setup_student(self, first_name='', last_name='', authenticate=False, institution=None):
        user = self._setup_user(first_name, last_name, authenticate, institution=institution)
        self._add_eduid_socialaccount(user)
        return user


    def enroll_user(self, recipient, badgeclass):
        assertion_post_data = {"email": "test@example.com",
                               "badge_class": badgeclass.entity_id,
                               "recipients": [{'selected': True,
                                               'recipient_name': 'Piet Jonker',
                                               'recipient_type': 'id',
                                               'recipient_identifier': recipient.get_recipient_identifier()
                                               }]}
        StudentsEnrolled.objects.create(user=recipient,
                                        badge_class_id=badgeclass.pk,
                                        date_consent_given=timezone.now())
        return assertion_post_data

    def setup_institution(self):
        return Institution.objects.create(name=name_randomiser('Test Institution'))

    def setup_faculty(self, institution=None):
        if not institution:
            institution = self.setup_institution()
        return Faculty.objects.create(name=name_randomiser('Test Issuer'), institution=institution)

    def setup_issuer(self, created_by, faculty=None):
        if not faculty:
            faculty = self.setup_faculty()
        return Issuer.objects.create(name=name_randomiser('Test Issuer'),
                                     description='description',
                                     created_by=created_by,
                                     faculty=faculty)

    def setup_badgeclass(self, issuer=None, image=None):
        name = 'Test Badgeclass #{}'.format(random.random)
        if image is None:
            image = open(self.get_test_image_path(), 'r')
        if not issuer:
            issuer = self.setup_issuer()
        return BadgeClass.objects.create(
            issuer=issuer,
            image=image,
            name=name,
            description='Description',
            criteria_text='Criteria text'
        )

    def setup_staff_membership(self, user, object, may_create=False, may_read=False,
                               may_update=False, may_delete=False, may_award=False,
                               may_sign=False, may_administrate_users=False):
        if object.__class__.__name__ == 'Institution':
            staff = InstitutionStaff.objects.get(user=user, institution=object)
        elif object.__class__.__name__ == 'Faculty':
            staff, created = FacultyStaff.objects.get_or_create(user=user, faculty=object)
        elif object.__class__.__name__ == 'Issuer':
            staff, created = IssuerStaff.objects.get_or_create(user=user, issuer=object)
        elif object.__class__.__name__ == 'BadgeClass':
            staff, created = BadgeClassStaff.objects.get_or_create(user=user, badgeclass = object)
        else:
            raise ValueError('Object class not valid choice')
        staff.may_create = may_create
        staff.may_update = may_update
        staff.may_read = may_read
        staff.may_delete = may_delete
        staff.may_award = may_award
        staff.may_sign = may_sign
        staff.may_administrate_users = may_administrate_users
        staff.save()
        return staff

    # def setup_badgeclasses(self, how_many=3, **kwargs):
    #     for i in range(0, how_many):
    #         yield self.setup_badgeclass(**kwargs)
    #
    # def get_testfiles_path(self, *args):
    #     return os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', *args)
    #
    # def get_test_image_path(self):
    #     return os.path.join(self.get_testfiles_path(), 'guinea_pig_testing_badge.png')
    #
    # def get_test_svg_image_path(self):
    #     return os.path.join(self.get_testfiles_path(), 'test_badgeclass.svg')








@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    },
)
class CachingTestCase(TransactionTestCase):
    @classmethod
    def tearDownClass(cls):
        test_cache = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        test_cache.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    HTTP_ORIGIN="http://localhost:8000",
    BADGR_APP_ID=1,
    CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}
}
)
class BadgrTestCase(SetupHelper, APITransactionTestCase, CachingTestCase):
    def setUp(self):
        super(BadgrTestCase, self).setUp()

        from django.conf import settings
        badgr_app_id = getattr(settings, 'BADGR_APP_ID')
        try:
            self.badgr_app = BadgrApp.objects.get(pk=badgr_app_id)
        except BadgrApp.DoesNotExist:
            self.badgr_app = BadgrApp.objects.create(
                name='test cors',
                cors='localhost:8000')

        self.assertEqual(self.badgr_app.pk, badgr_app_id)