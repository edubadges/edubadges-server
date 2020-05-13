# encoding: utf-8


import os
import random
import uuid
import string
from graphene.test import Client as GrapheneClient
from rest_framework.test import APITransactionTestCase


from allauth.socialaccount.models import SocialAccount
from badgeuser.models import BadgeUser, TermsVersion
from django.test import override_settings
from django.utils import timezone
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite import TOP_DIR
from mainsite.models import BadgrApp
from mainsite.schema import schema
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class GrapheneMockContext(object):
    def __init__(self, user):
        self.user = user

def name_randomiser(name):
    s = ''.join(random.choices(string.ascii_lowercase, k=10))
    return name + '_' + s


class SetupHelper(object):

    def graphene_post(self, user, query):
        client = GrapheneClient(schema)
        return client.execute(query, context_value=GrapheneMockContext(user))

    def get_testfiles_path(self, *args):
        return os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', *args)

    def get_test_image_path(self):
        return os.path.join(self.get_testfiles_path(), 'guinea_pig_testing_badge.png')

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

    def authenticate(self, user):
        return self.client._login(user, backend='oauth2_provider.backends.OAuth2Backend')

    def setup_teacher(self, first_name='', last_name='', authenticate=False, institution=None):
        user = self._setup_user(first_name, last_name, authenticate, institution=institution)
        self._add_surfconext_socialaccount(user)
        user.is_teacher = True
        user.save()
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

    def setup_badgeclass(self, issuer, image=None):
        name = 'Test Badgeclass #{}'.format(random.random)
        if image is None:
            image = open(self.get_test_image_path(), 'r')
        return BadgeClass.objects.create(
            issuer=issuer,
            image=image,
            name=name,
            description='Description',
            criteria_text='Criteria text'
        )

    def setup_assertion(self, recipient, badgeclass, created_by):
        recipient_id = recipient.get_recipient_identifier()
        return badgeclass.issue(recipient_id=recipient_id, created_by=created_by)

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

    def instance_is_removed(self, instance):
        try:
            instance.__class__.objects.get(pk=instance.pk)
            return False
        except instance.__class__.DoesNotExist:
            return True


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    HTTP_ORIGIN="http://localhost:8000",
    BADGR_APP_ID=1,
    # CACHES={'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
)
class BadgrTestCase(SetupHelper, APITransactionTestCase):
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