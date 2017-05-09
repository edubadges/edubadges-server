# encoding: utf-8
from __future__ import unicode_literals

import random
import time

import os
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.test import override_settings, TransactionTestCase
from mainsite import TOP_DIR
from rest_framework.test import APITransactionTestCase

from badgeuser.models import BadgeUser
from issuer.models import Issuer, BadgeClass


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
                   send_confirmation=False):

        if email is None:
            email = 'setup_user_{}@email.test'.format(random.random())
        user = BadgeUser.objects.create(email=email,
                                        first_name=first_name,
                                        last_name=last_name,
                                        create_email_address=create_email_address,
                                        send_confirmation=send_confirmation)
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
        if authenticate:
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
)
class BadgrTestCase(SetupUserHelper, APITransactionTestCase, CachingTestCase):
    pass
