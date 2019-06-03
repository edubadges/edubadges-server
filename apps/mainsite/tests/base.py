# encoding: utf-8
from __future__ import unicode_literals

from datetime import timedelta
import os
import random
import time

from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.test import override_settings, TransactionTestCase
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application
from rest_framework.test import APITransactionTestCase

from badgeuser.models import BadgeUser, TermsVersion
from issuer.models import Issuer, BadgeClass
from mainsite import TOP_DIR
from mainsite.models import BadgrApp, ApplicationInfo
from allauth.socialaccount.models import SocialAccount

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


class SetupUserHelper(object):
    def setup_user(self,
                   email=None,
                   first_name='firsty',
                   last_name='lastington',
                   password='secret',
                   authenticate=False,
                   create_email_address=True,
                   verified=True,
                   primary=True,
                   send_confirmation=False,
                   token_scope=None,
                   terms_version=1,
                   eduid=None
                   ):


        if email is None:
            email = 'setup_user_{}@email.test'.format(random.random())
        user = BadgeUser.objects.create(email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        create_email_address=create_email_address,
                                        send_confirmation=send_confirmation)

        if terms_version is not None:
            # ensure there are terms and the user agrees to them to ensure there are no cache misses during tests
            terms, created = TermsVersion.objects.get_or_create(version=terms_version)
            user.agreed_terms_version = terms_version
            user.save()

        if password is None:
            user.password = None
        else:
            user.set_password(password)
            user.save()
        if create_email_address:
            email = user.cached_emails()[0]
            email.verified = verified
            email.primary = primary
            email.save()
            add_social_account_to_user(user, email.email, eduid=eduid)

        if token_scope:
            app = Application.objects.create(
                client_id='test', client_secret='testsecret', authorization_grant_type='client-credentials',  # 'authorization-code'
                user=user)
            token = AccessToken.objects.create(
                user=user, scope=token_scope, expires=timezone.now() + timedelta(hours=1),
                token='prettyplease', application=app
            )
            self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token.token))
        elif authenticate:
            self.client.force_authenticate(user=user)
        return user


class SetupIssuerHelper(object):
    def setup_issuer(self,
                     name='Test Issuer',
                     description='test case Issuer',
                     owner=None):
        issuer = Issuer.objects.create(name=name, description=description, created_by=owner)
        return issuer

    def get_testfiles_path(self, *args):
        return os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', *args)

    def get_test_image_path(self):
        return os.path.join(self.get_testfiles_path(), 'guinea_pig_testing_badge.png')

    def get_test_svg_image_path(self):
        return os.path.join(self.get_testfiles_path(), 'test_badgeclass.svg')

    def setup_badgeclass(self,
                         issuer,
                         name=None,
                         image=None,
                         description='test case badgeclass',
                         criteria_text='do something',
                         criteria_url=None):

        if name is None:
            name = 'Test Badgeclass #{}'.format(random.random)

        if image is None:
            image = open(self.get_test_image_path(), 'r')

        badgeclass = BadgeClass.objects.create(
            issuer=issuer,
            image=image,
            name=name,
            description=description,
        )
        return badgeclass

    def setup_badgeclasses(self, how_many=3, **kwargs):
        for i in range(0, how_many):
            yield self.setup_badgeclass(**kwargs)




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
)
class BadgrTestCase(SetupUserHelper, APITransactionTestCase, CachingTestCase):
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

        self.assertEquals(self.badgr_app.pk, badgr_app_id)

def add_social_account_to_user(user, email, eduid=None):
    extra_data = {"family_name": "Neci",
                  "sub": "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18" if not eduid else eduid,
                  "email": email,
                  "name": "Er\u00f4ss Neci",
                  "given_name": "Er\u00f4ss"}

    socialaccount = SocialAccount(extra_data=extra_data,
                                  uid="urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18" if not eduid else eduid,
                                  provider='edu_id',
                                  user=user)
    socialaccount.save()