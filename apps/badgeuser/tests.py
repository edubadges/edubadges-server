import random
import re
import unittest
import os
from django.contrib.auth import SESSION_KEY
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import override_settings
from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token

from badgeuser.authcode import encrypt_authcode, decrypt_authcode, authcode_for_accesstoken
from mainsite import TOP_DIR
from rest_framework.authtoken.models import Token

from badgeuser.models import BadgeUser, BadgrAccessToken
from badgeuser.models import EmailAddressVariant, CachedEmailAddress
from issuer.models import BadgeClass, Issuer
from mainsite.models import BadgrApp, ApplicationInfo
from mainsite.tests.base import BadgrTestCase


class AuthTokenTests(BadgrTestCase):

    @unittest.skip('For debug speedup')
    def test_create_user_auth_token(self):
        """
        Ensure that get can create a token for a user that doesn't have one
        and that it doesn't modify a token for a user that already has one.
        """

        self.setup_user(authenticate=True)

        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)
        token = response.data.get('token')
        self.assertRegexpMatches(token, r'[\da-f]{40}')

        second_response = self.client.get('/v1/user/auth-token')
        self.assertEqual(token, second_response.data.get('token'))

    @unittest.skip('For debug speedup')
    def test_update_user_auth_token(self):
        """
        Ensure that a PUT request updates a user token.
        """
        # Create a token for the first time.
        user = self.setup_user(authenticate=True)

        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)
        token = response.data.get('token')
        self.assertRegexpMatches(token, r'[\da-f]{40}')

        # Ensure that token has changed.
        second_response = self.client.put('/v1/user/auth-token')
        self.assertNotEqual(token, second_response.data.get('token'))
        self.assertTrue(second_response.data.get('replace'))

        self.assertEqual(user.cached_token(), second_response.data.get('token'))
        self.assertEqual(Token.objects.get(user=user).key, user.cached_token())


class UserCreateTests(BadgrTestCase):

    @unittest.skip('For debug speedup')
    def test_create_user(self):
        user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuniqueuser1@example.com',
            'password': 'secr3t4nds3cur3'
        }

        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    @unittest.skip('For debug speedup')
    def test_create_user_with_already_claimed_email(self):
        email = 'test2@example.com'
        user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': email,
            'password': '123456'
        }
        existing_user = self.setup_user(email=email, authenticate=False, create_email_address=True)

        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    @unittest.skip('For debug speedup')
    def test_can_create_user_with_preexisting_unconfirmed_email(self):
        email = 'unclaimed1@example.com'
        user_data = {
            'first_name': 'NEW Test',
            'last_name': 'User',
            'email': email,
            'password': 'secr3t4nds3cur3'
        }

        # create an existing user that owns email -- but unverified
        existing_user = self.setup_user(email=email, password='secret', authenticate=False, verified=False)
        existing_user_pk = existing_user.pk
        existing_email = existing_user.cached_emails()[0]
        self.assertEqual(existing_email.email, email)
        self.assertFalse(existing_email.verified)

        # attempt to signup with the same email
        response = self.client.post('/v1/user/profile', user_data)

        # should work successfully and a confirmation email  sent
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        # the user with this email should be the new signup
        new_user = BadgeUser.objects.get(email=email)
        self.assertEqual(new_user.email, email)
        self.assertEqual(new_user.first_name, user_data.get('first_name'))
        self.assertEqual(new_user.last_name, user_data.get('last_name'))
        existing_email = CachedEmailAddress.objects.get(email=email)
        self.assertEqual(existing_email.user, new_user)

        # the old user should no longer exist
        with self.assertRaises(BadgeUser.DoesNotExist):
            old_user = BadgeUser.objects.get(pk=existing_user_pk)

    @unittest.skip('For debug speedup')
    def test_user_can_not_add_secondary_email_of_preexisting_unclaimed_email(self):
        email = "unclaimed2@example.com"
        first_user = self.setup_user(authenticate=False)
        CachedEmailAddress.objects.create(user=first_user, email=email, primary=False, verified=False)

        second_user = self.setup_user(email='second@user.fake', authenticate=True,
                                      eduid='edu_id-urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bc')
        response = self.client.post('/v1/user/emails', {'email': email})
        self.assertEqual(response.status_code, 400)

    @unittest.skip('For debug speedup')
    def test_can_create_account_with_same_email_since_deleted(self):
        email = 'unclaimed1@example.com'
        new_email = 'newjunkeremail@junk.net'
        first_user_data = user_data = {
            'first_name': 'NEW Test',
            'last_name': 'User',
            'email': email,
            'password': 'secr3t4nds3cur3'
        }
        response = self.client.post('/v1/user/profile', user_data)

        first_user = BadgeUser.objects.get(email=email)
        first_email = CachedEmailAddress.objects.get(email=email)
        first_email.verified = True
        first_email.save()

        second_email = CachedEmailAddress(email=new_email, user=first_user, verified=True)
        second_email.save()

        self.assertEqual(len(first_user.cached_emails()), 2)

        self.client.force_authenticate(user=first_user)
        response = self.client.put(
            reverse('v1_api_user_email_detail', args=[second_email.pk]),
            {'primary': True}
        )
        self.assertEqual(response.status_code, 200)

        # Reload user and emails
        first_user = BadgeUser.objects.get(email=new_email)
        first_email = CachedEmailAddress.objects.get(email=email)
        second_email = CachedEmailAddress.objects.get(email=new_email)

        self.assertEqual(first_user.email, new_email)
        self.assertTrue(second_email.primary)
        self.assertFalse(first_email.primary)

        self.assertTrue(email in [e.email for e in first_user.cached_emails()])
        first_email.delete()
        self.assertFalse(email in [e.email for e in first_user.cached_emails()])

        user_data['name'] = 'NEWEST Test'
        self.client.force_authenticate(user=None)
        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 201)

    @unittest.skip('For debug speedup')
    def test_shouldnt_error_when_user_exists_with_email(self):
        email = 'existing3@example.test'

        old_user = self.setup_user(email=email, password='secret2')  # password is set because its an existing user

        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secret',
            'email': email
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    @unittest.skip('For debug speedup')
    def test_autocreated_user_can_signup(self):
        email = 'existing4@example.test'

        old_user = self.setup_user(email=email, password=None, create_email_address=False)  # no password set

        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secr3t4nds3cur3',
            'email': email
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    @unittest.skip('For debug speedup')
    def test_should_signup_with_email_with_plus(self):
        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secr3t4nds3cur3',
            'email': 'nonexistent23+extra@test.nonexistent'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    @unittest.skip('For debug speedup')
    def test_should_signup_with_email_with_uc_email(self):
        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secr3t4nds3cur3',
            'email': 'VERYNONEXISTENT@test.nonexistent'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)


class UserUnitTests(BadgrTestCase):
    def test_user_can_have_unicode_characters_in_name(self):
        user = BadgeUser(
            username='abc', email='abc@example.com',
            first_name=u'\xe2', last_name=u'Bowie')

        self.assertEqual(user.get_full_name(), u'\xe2 Bowie')


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
)
class UserEmailTests(BadgrTestCase):
    def setUp(self):
        super(UserEmailTests, self).setUp()

        self.badgr_app = BadgrApp(cors='testserver',
                                  email_confirmation_redirect='http://testserver/login/',
                                  forgot_password_redirect='http://testserver/reset-password/')
        self.badgr_app.save()

        self.first_user_email = 'first.user@newemail.test'
        self.first_user_email_secondary = 'first.user+2@newemail.test'
        self.first_user = self.setup_user(email=self.first_user_email, authenticate=True)
        CachedEmailAddress.objects.create(user=self.first_user, email=self.first_user_email_secondary, verified=True)
        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)

    def test_user_register_new_email(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        starting_count = len(response.data)

        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(starting_count+1, len(response.data))

        # Mark email as verified
        email = CachedEmailAddress.cached.get(email='new+email@newemail.com')
        email.verified = True
        email.save()

        # Can not add the same email twice
        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 400)
        self.assertTrue("Could not register email address." in response.data)

    def test_user_can_verify_new_email(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        starting_count = len(response.data)

        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(starting_count+1, len(response.data))

        with self.settings(BADGR_APP_ID=self.badgr_app.id):
            # Mark email as verified
            email = CachedEmailAddress.cached.get(email='new+email@newemail.com')
            self.assertEqual(len(mail.outbox), 1)
            verify_url = re.search("(?P<url>/v1/[^\s]+)", mail.outbox[0].body).group("url")
            response = self.client.get(verify_url)
            self.assertEqual(response.status_code, 302)

        email = CachedEmailAddress.cached.get(email='new+email@newemail.com')
        self.assertTrue(email.verified)

    def test_user_cant_register_new_email_verified_by_other(self):
        second_user = self.setup_user(authenticate=False)
        existing_mail = CachedEmailAddress.objects.create(
            user=self.first_user, email='new+email@newemail.com', verified=True)

        response = self.client.get('/v1/user/emails')

        self.assertEqual(response.status_code, 200)
        starting_count = len(response.data)

        # Another user tries to add this email
        self.client.force_authenticate(user=second_user)
        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 400)

        self.client.force_authenticate(user=self.first_user)
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(starting_count, len(response.data))

    def test_user_can_remove_email(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)

        not_primary = random.choice(filter(lambda e: e['verified'] and not e['primary'], response.data))
        primary = random.choice(filter(lambda e: e['primary'], response.data))

        # cant remove primary email
        response = self.client.delete('/v1/user/emails/{}'.format(primary.get('id')))
        self.assertEqual(response.status_code, 400)
        response = self.client.get('/v1/user/emails/{}'.format(primary.get('id')))
        self.assertEqual(response.status_code, 200)

        # can remove a non-primary email
        response = self.client.delete('/v1/user/emails/{}'.format(not_primary.get('id')))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/v1/user/emails/{}'.format(not_primary.get('id')))
        self.assertEqual(response.status_code, 404)

    def test_user_can_make_email_primary(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)

        self.assertGreater(len(response.data), 0)

        not_primary = random.choice(filter(lambda e: e['verified'] and not e['primary'], response.data))

        # set a non primary email to primary
        response = self.client.put('/v1/user/emails/{}'.format(not_primary.get('id')), {
            'primary': True
        })
        self.assertEqual(response.status_code, 200)

        # confirm that the new email is primary and the others aren't
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        for email in response.data:
            if email['id'] == not_primary['id']:
                self.assertEqual(email['primary'], True)
            else:
                self.assertEqual(email['primary'], False)

    def test_user_can_resend_verification_email(self):
        # register a new un-verified email
        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        not_verified = random.choice(filter(lambda e: not e['verified'], response.data))
        verified = random.choice(filter(lambda e: e['verified'], response.data))

        # dont resend verification email if already verified
        response = self.client.put('/v1/user/emails/{}'.format(verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        # gets an email for an unverified email
        response = self.client.put('/v1/user/emails/{}'.format(not_verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    def test_user_can_request_forgot_password(self):
        self.client.logout()

        # dont send recovery to unknown emails
        response = self.client.post('/v1/user/forgot-password', {
            'email': 'unknown-test2@example.com.fake',
        })
        self.assertEqual(response.status_code, 200, "Does not leak information about account emails")
        self.assertEqual(len(mail.outbox), 0)

        with self.settings(BADGR_APP_ID=self.badgr_app.id):
            # successfully send recovery email
            response = self.client.post('/v1/user/forgot-password', {
                'email': self.first_user_email
            })
            self.assertEqual(response.status_code, 200)
            # received email with recovery url
            self.assertEqual(len(mail.outbox), 1)
            matches = re.search(r'/v1/user/forgot-password\?token=([-0-9a-zA-Z]*)', mail.outbox[0].body)
            self.assertIsNotNone(matches)
            token = matches.group(1)
            new_password = 'new-password-ee'

            # able to use token received in email to reset password
            response = self.client.put('/v1/user/forgot-password', {
                'token': token,
                'password': new_password
            })
            self.assertEqual(response.status_code, 200)

            response = self.client.post('/api-auth/token', {
                'username': self.first_user.username,
                'password': new_password,
            })
            self.assertEqual(response.status_code, 200)

    def test_lower_variant_autocreated_on_new_email(self):
        first_email = CachedEmailAddress(
            email="HelloAgain@world.com", user=BadgeUser.objects.first(), verified=True
        )
        first_email.save()
        self.assertIsNotNone(first_email.pk)

        variants = EmailAddressVariant.objects.filter(canonical_email=first_email)

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].email, 'helloagain@world.com')

    def test_can_create_new_variant_api(self):
        user = BadgeUser.objects.first()
        first_email = CachedEmailAddress(
            email="helloagain@world.com", user=user, verified=True
        )
        first_email.save()
        self.assertIsNotNone(first_email.pk)

        self.client.force_authenticate(user=user)
        response = self.client.post('/v1/user/emails', {'email': 'HelloAgain@world.com'})

        self.assertEqual(response.status_code, 400)
        self.assertTrue('Matching address already exists. New case variant registered.' in response.data)

        variants = first_email.cached_variants()
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].email, 'HelloAgain@world.com')

    def test_can_create_variants(self):
        user = self.setup_user(authenticate=False)
        first_email = CachedEmailAddress.objects.create(email="test@example.com", verified=True, user=user)
        self.assertIsNotNone(first_email.pk)

        first_variant_email = "TEST@example.com"
        second_variant_email = "Test@example.com"

        first_variant = EmailAddressVariant(email=first_variant_email, canonical_email=first_email)
        first_variant.save()
        self.assertEqual(first_variant.canonical_email, first_email)

        second_variant = first_email.add_variant(second_variant_email)
        self.assertEqual(second_variant.canonical_email, first_email)

        self.assertEqual(len(first_email.emailaddressvariant_set.all()), 2)
        self.assertEqual(len(first_email.cached_variants()), 2)

    def test_user_can_create_variant_method(self):
        user = BadgeUser.objects.first()
        first_email = CachedEmailAddress(
            email="howdy@world.com", user=user, verified=True
        )
        first_email.save()
        first_email.add_variant("HOWDY@world.com")

        self.assertTrue(user.can_add_variant("Howdy@world.com"))
        self.assertFalse(user.can_add_variant("HOWDY@world.com"))  # already exists
        self.assertFalse(user.can_add_variant("howdy@world.com"))  # is the original
        self.assertFalse(user.can_add_variant("howdyfeller@world.com"))  # not a match of original

    def test_can_create_variant_for_unconfirmed_email(self):
        user = BadgeUser.objects.first()
        new_email_address = "new@unconfirmed.info"
        new_email = CachedEmailAddress.objects.create(email=new_email_address, user=user)
        new_variant = EmailAddressVariant(email=new_email_address.upper(), canonical_email=new_email)

        new_variant.save()
        self.assertFalse(new_variant.verified)

        verified_emails = [e.email for e in user.emailaddress_set.filter(verified=True)] \
                          + [e.email for e in user.cached_email_variants() if e.verified]

        self.assertTrue(new_variant not in verified_emails)

    def cannot_link_variant_of_case_insensitive_nonmatch(self):
        first_email = CachedEmailAddress.objects.get(email="test@example.com")
        self.assertIsNotNone(first_email.pk)

        variant_email = "NOMATCH@example.com"

        variant = EmailAddressVariant(email=variant_email, canonical_email=first_email)
        try:
            variant.save()
        except ValidationError as e:
            self.assertEqual(e.message, "New EmailAddressVariant does not match stored email address.")
        else:
            raise self.fail("ValidationError expected on nonmatch.")

@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
)
class UserBadgeTests(BadgrTestCase):
    def setUp(self):
        super(UserBadgeTests, self).setUp()
        self.badgr_app = BadgrApp(cors='testserver',
                                  email_confirmation_redirect='http://testserver/login/',
                                  forgot_password_redirect='http://testserver/reset-password/')
        self.badgr_app.save()

    def create_badgeclass(self):
        with open(os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', 'guinea_pig_testing_badge.png'), 'r') as fh:
            issuer = Issuer.objects.create(name='Issuer of Testing')
            badgeclass = BadgeClass.objects.create(
                issuer=issuer,
                name="Badge of Testing",
                image=SimpleUploadedFile(name='test_image.png', content=fh.read(), content_type='image/png')
            )
            return badgeclass

    @unittest.skip('For debug speedup')
    def test_badge_awards_transferred_on_email_verification(self):
        first_user_email = 'first+user@email.test'
        first_user = self.setup_user(email=first_user_email, authenticate=True)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        starting_count = len(response.data)

        badgeclass = self.create_badgeclass()
        badgeclass.issue(recipient_id='New+email@newemail.com', allow_uppercase=True)
        badgeclass.issue(recipient_id='New+Email@newemail.com', allow_uppercase=True)

        outbox_count = len(mail.outbox)

        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(starting_count+1, len(response.data))

        with self.settings(BADGR_APP_ID=self.badgr_app.id):
            # Mark email as verified
            email = CachedEmailAddress.cached.get(email='new+email@newemail.com')
            self.assertEqual(len(mail.outbox), outbox_count+1)
            verify_url = re.search("(?P<url>/v1/[^\s]+)", mail.outbox[-1].body).group("url")
            response = self.client.get(verify_url)
            self.assertEqual(response.status_code, 302)

        email = CachedEmailAddress.cached.get(email='new+email@newemail.com')
        self.assertTrue(email.verified)

        self.assertTrue('New+email@newemail.com' in [e.email for e in email.cached_variants()])
        self.assertTrue('New+Email@newemail.com' in [e.email for e in email.cached_variants()])


@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
)
class UserProfileTests(BadgrTestCase):

    def test_user_can_change_profile(self):
        first = 'firsty'
        last = 'lastington'
        new_password = 'new-password'
        username = 'testinguser'
        original_password = 'password'
        email = 'testinguser@testing.info'

        user = BadgeUser(username=username, is_active=True, email=email)
        user.set_password(original_password)
        user.save()
        self.client.login(username=username, password=original_password)
        self.assertUserLoggedIn()

        response = self.client.put('/v1/user/profile', {
            'first_name': first,
            'last_name': last,
            'password': new_password,
            'current_password': original_password
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first, response.data.get('first_name'))
        self.assertEqual(last, response.data.get('last_name'))

        self.client.logout()
        self.client.login(username=username, password=new_password)
        self.assertUserLoggedIn()
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.put('/v1/user/profile', {
            'first_name': 'Barry',
            'last_name': 'Manilow'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual('Barry', response.data.get('first_name'))

        third_password = 'superstar!'
        response = self.client.put('/v1/user/profile', {
            'password': third_password,
            'current_password': new_password
        })
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        self.client.login(username=username, password=third_password)
        self.assertUserLoggedIn()

    def assertUserLoggedIn(self, user_pk=None):
        self.assertIn(SESSION_KEY, self.client.session)
        if user_pk is not None:
            self.assertEqual(self.client.session[SESSION_KEY], user_pk)

