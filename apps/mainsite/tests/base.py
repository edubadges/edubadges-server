# encoding: utf-8

import base64
import os
import random
import uuid
import string
from graphene.test import Client as GrapheneClient
from rest_framework.test import APITransactionTestCase


from allauth.socialaccount.models import SocialAccount
from badgeuser.models import BadgeUser, Terms, TermsUrl
from directaward.models import DirectAward
from django.utils import timezone
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite import TOP_DIR
from mainsite.models import BadgrApp
from mainsite.schema import schema
from mainsite.utils import resize_image
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class GrapheneMockContext(object):
    def __init__(self, user):
        self.user = user


def string_randomiser(name, prefix=False):
    s = ''.join(random.choices(string.ascii_lowercase, k=10))
    if not prefix:
        return name + '_' + s
    else:
        return s + '_' + name


class SetupHelper(object):

    def graphene_post(self, user, query):
        client = GrapheneClient(schema)
        return client.execute(query, context_value=GrapheneMockContext(user))

    def get_testfiles_path(self, *args):
        return os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', *args)

    def get_test_image_path(self):
        return os.path.join(self.get_testfiles_path(), 'guinea_pig_testing_badge.png')

    def get_test_image_path_too_large(self):
        return os.path.join(self.get_testfiles_path(),'too_large_test_image.png')

    def add_eduid_socialaccount(self, user, affiliations):
        random_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:{}c14-b952-4d7e-85fd-{}ac5c6f18".format(random.randint(1, 99999), random.randint(1, 9999))
        extra_data = {"family_name": user.last_name,
                      "sub": random_eduid,
                      "email": user.email,
                      "name": user.get_full_name(),
                      "given_name": user.first_name,
                      'eduperson_scoped_affiliation': affiliations}
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

    def get_image_data(self, path):
        with open(path, 'rb') as file:
            return "data:image/jpg;base64,%s" % base64.b64encode(file.read()).decode()

    def _make_email_primary(self, user):
        email = user.cached_emails()[0]
        email.verified = True
        email.primary = True
        email.save()

    def setup_user(self, first_name='firsty', last_name='lastington', authenticate=False, institution=None, email=None):
        if not email:
            email = 'setup_user_{}@email.test'.format(random.random())
        if not institution:
            institution = self.setup_institution()
        user = BadgeUser.objects.create(email=email,
                                        first_name=first_name,
                                        last_name=last_name)
        user.institution = institution
        user.validated_name = f"{first_name} {last_name}"
        user.save()
        self._make_email_primary(user)
        if authenticate:
            self.client.force_authenticate(user=user)
        return user

    def authenticate(self, user):
        self.client.logout()
        return self.client._login(user, backend='oauth2_provider.backends.OAuth2Backend')

    def setup_teacher(self, first_name='', last_name='', authenticate=False, institution=None, email=None):
        if not first_name:
            first_name = string_randomiser('FirstName')
        if not last_name:
            last_name = string_randomiser('LastName')
        user = self.setup_user(first_name, last_name, authenticate, institution=institution, email=email)
        self._add_surfconext_socialaccount(user)
        user.is_teacher = True
        user.save()
        return user

    def setup_student(self, first_name='', last_name='', authenticate=False, affiliated_institutions=[]):
        first_name = string_randomiser('student_first_name') if not first_name else first_name
        last_name = string_randomiser('student_last_name') if not last_name else last_name
        user = self.setup_user(first_name, last_name, authenticate, institution=None)
        affiliations = ['affiliate@'+institution.identifier for institution in affiliated_institutions]
        self.add_eduid_socialaccount(user, affiliations=affiliations)
        return user

    def setup_direct_award(self, badgeclass, **kwargs):
        if not kwargs.get('recipient_email', False):
            kwargs['recipient_email'] = string_randomiser('some@amail.com', prefix=True)
        if not kwargs.get('eppn', False):
            kwargs['eppn'] = string_randomiser('eppn')
        direct_award = DirectAward.objects.create(badgeclass=badgeclass, **kwargs)
        badgeclass.remove_cached_data(['cached_direct_awards'])
        return direct_award


    def enroll_user(self, recipient, badgeclass):
        return StudentsEnrolled.objects.create(user=recipient,
                                        badge_class_id=badgeclass.pk,
                                        date_consent_given=timezone.now())

    def _setup_institution_terms(self, institution):
        formal_badge, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_FORMAL_BADGE)
        TermsUrl.objects.get_or_create(terms=formal_badge, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=False,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md")
        TermsUrl.objects.get_or_create(terms=formal_badge, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md")
        TermsUrl.objects.get_or_create(terms=formal_badge, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md")
        TermsUrl.objects.get_or_create(terms=formal_badge, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md")
        informal_badge, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_INFORMAL_BADGE)
        TermsUrl.objects.get_or_create(terms=informal_badge, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=False,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md")
        TermsUrl.objects.get_or_create(terms=informal_badge, language=TermsUrl.LANGUAGE_DUTCH, excerpt=False,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-nl.md")
        TermsUrl.objects.get_or_create(terms=informal_badge, language=TermsUrl.LANGUAGE_ENGLISH, excerpt=True,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md")
        TermsUrl.objects.get_or_create(terms=informal_badge, language=TermsUrl.LANGUAGE_DUTCH, excerpt=True,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-nl.md")
        institution.remove_cached_data(['cached_terms'])

    def increment_general_terms_version(self, user):
        general_terms = Terms.get_general_terms(user)
        for general_term in general_terms:
            general_term.version += general_term.version
            general_term.save()

    def setup_general_terms(self):
        terms_of_service, _ = Terms.objects.get_or_create(version=1, institution=None,
                                                          terms_type=Terms.TYPE_TERMS_OF_SERVICE)
        TermsUrl.objects.get_or_create(terms=terms_of_service,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_DUTCH)
        TermsUrl.objects.get_or_create(terms=terms_of_service,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_ENGLISH)
        terms_service_agreement_student, _ = Terms.objects.get_or_create(version=1, institution=None,
                                                                         terms_type=Terms.TYPE_SERVICE_AGREEMENT_STUDENT)
        TermsUrl.objects.get_or_create(terms=terms_service_agreement_student,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_DUTCH)
        TermsUrl.objects.get_or_create(terms=terms_service_agreement_student,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_ENGLISH)
        terms_service_agreement_employee, _ = Terms.objects.get_or_create(version=1, institution=None,
                                                                          terms_type=Terms.TYPE_SERVICE_AGREEMENT_EMPLOYEE)
        TermsUrl.objects.get_or_create(terms=terms_service_agreement_employee,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_DUTCH)
        TermsUrl.objects.get_or_create(terms=terms_service_agreement_employee,
                                       url="https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-principles-en.md",
                                       language=TermsUrl.LANGUAGE_ENGLISH)

    def setup_institution(self, **kwargs):
        if not kwargs.get('name_english', False):
            kwargs['name_english'] = string_randomiser('Test Institution')
        if not kwargs.get('identifier', False):
            kwargs['identifier'] = kwargs['name_english']
        institution = Institution.objects.create(**kwargs)
        self._setup_institution_terms(institution)
        return institution

    def setup_faculty(self, **kwargs):
        if not kwargs.get('institution', False):
            kwargs['institution'] = self.setup_institution()
        if not kwargs.get('name_english', False) and not kwargs.get('name_dutch', False):
            kwargs['name_english'] = string_randomiser('Test Faculty')
        return Faculty.objects.create(**kwargs)

    def setup_issuer(self, created_by, **kwargs):
        if not kwargs.get('faculty', False):
            kwargs['faculty'] = self.setup_faculty(institution=created_by.institution)
        if not kwargs.get('name_english', False):
            kwargs['name_english'] = string_randomiser('Test Issuer'),
        image_english = resize_image(open(self.get_test_image_path(), 'r'))
        return Issuer.objects.create(description_english='description',
                                     description_dutch='description',
                                     created_by=created_by,
                                     image_english=image_english,
                                     **kwargs)

    def setup_badgeclass(self, issuer, **kwargs):
        if not kwargs.get('name', False):
            kwargs['name'] = 'Test Badgeclass #{}'.format(random.random())
        if not kwargs.get('image', False):
            kwargs['image'] = resize_image(open(self.get_test_image_path(), 'r'))
        return BadgeClass.objects.create(
            issuer=issuer,
            formal=False,
            description='Description',
            criteria_text='Criteria text',
            **kwargs
        )

    def setup_assertion(self, recipient, badgeclass, created_by, **kwargs):
        return badgeclass.issue(recipient=recipient, created_by=created_by, **kwargs)

    def setup_staff_membership(self, user, object, may_create=False, may_read=False,
                               may_update=False, may_delete=False, may_award=False,
                               may_sign=False, may_administrate_users=False):
        if object.__class__.__name__ == 'Institution':
            staff = InstitutionStaff(institution=object)
        elif object.__class__.__name__ == 'Faculty':
            staff = FacultyStaff(faculty=object)
        elif object.__class__.__name__ == 'Issuer':
            staff = IssuerStaff(issuer=object)
        elif object.__class__.__name__ == 'BadgeClass':
            staff = BadgeClassStaff(badgeclass = object)
        else:
            raise ValueError('Object class not valid choice')
        staff.user = user
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

    def reload_from_db(self, instance):
        return instance.__class__.objects.get(pk=instance.pk)


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
        self.setup_general_terms()

        self.assertEqual(self.badgr_app.pk, badgr_app_id)