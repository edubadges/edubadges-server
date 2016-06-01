# Created by wiggins@concentricsky.com on 4/16/16.
import json
import os
import time

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass, BadgeInstance
from issuer.serializers import BadgeInstanceSerializer
from mainsite import TOP_DIR
from mainsite.utils import OriginSetting
from pathway.completionspec import CompletionRequirementSpecFactory
from pathway.models import Pathway, PathwayElement
from pathway.serializers import PathwaySerializer, PathwayElementSerializer
from recipient.models import RecipientProfile, RecipientGroupMembership, RecipientGroup

CACHE_OVERRIDE = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
    }
}

@override_settings(CACHES = CACHE_OVERRIDE)
class CachingTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        test_cache = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        test_cache.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))


class PathwayApiTests(APITestCase, CachingTestCase):

    def setUp(self):
        super(PathwayApiTests, self).setUp()

        # instructor
        self.instructor = BadgeUser(username='instructor', email='instructor@local.test')
        self.instructor.set_password('secret')
        self.instructor.save()
        EmailAddress(email='instructor@local.test', verified=True, primary=True, user=self.instructor).save()
        self.assertTrue(self.client.login(username='instructor', password='secret'), "Instructor can log in")

        # issuer
        issuer_data = {
            'name': 'Unit Test Issuer',
            'description': "Issuer from unit test",
            'url': "http://example.test",
            'email': "unittest@example.test",
        }
        response = self.client.post(reverse('issuer_list'), issuer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created an issuer")
        self.assertTrue(response.data['slug'], "Received an issuer with a slug")
        self.issuer = response.data

    def test_can_create_pathway(self):
        pathway_data = {
            'name': "Test Career Pathway",
            'description': "Students pathway through the testing career",
        }
        response = self.client.post(reverse('pathway_list', kwargs={'issuer_slug': self.issuer.get('slug')}), pathway_data, format='json')
        pathway = response.data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway")

        # Plumber
        # plumbing badges
        with open(os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', 'guinea_pig_testing_badge.png')) as badge_image:
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Plumber",
                'description': "You plumb now",
                'criteria': "Learn what it is to be a plumber",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            plumber_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Intro Plumbing Badge",
                'description': "You learn to plumb",
                'criteria': "learn plumbing basics",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            intro_plumbing_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Advanced Plumbing 1 Badge",
                'description': "You plumb good 1",
                'criteria': "advanced plumbing method 1",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            adv1_plumbing_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Advanced Plumbing 2 Badge",
                'description': "You plumb good 2",
                'criteria': "advanced plumbing method 2",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            adv2_plumbing_badge = response.data

        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': pathway['rootElement'],
            'name': 'Plumber',
            'description': 'You can plumb things for people.',
            'completionBadge': plumber_badge['json']['id'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        plumber_element = response.data

        # Intro to Plumbing
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': plumber_element['@id'],
            'name': 'Intro to Plumbing',
            'description': 'You learn the basics of plumbing.',
            'requirements': {
                '@type': 'BadgeJunction',
                'junctionConfig': {
                    '@type': 'Conjunction',
                    'requiredNumber': 1,
                },
                'badges': [
                    intro_plumbing_badge['json']['id']
                ],
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        intro_plumbing_element = response.data

        # Advanced Plumbing (testing sending a json string for requirements)
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
             'parent': plumber_element['@id'],
             'name': 'Advanced Plumbing',
             'description': 'You learn all about plumbing.',
             'requirements': json.dumps({
                 '@type': 'BadgeJunction',
                 'junctionConfig': {
                     '@type': 'Disjunction',
                     'requiredNumber': 1,
                 },
                 'badges': [
                     adv1_plumbing_badge['json']['id'],
                     adv2_plumbing_badge['json']['id']
                 ],
             })
         }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        adv_plumbing_element = response.data

        # update requirements
        plumber_element.update({
            'requirements': {
                '@type': 'ElementJunction',
                'junctionConfig': {
                    '@type': 'Conjunction',
                    'requiredNumber': 2,
                },
                'elements': [
                    intro_plumbing_element['@id'],
                    adv_plumbing_element['@id']
                ],
            }
        })
        response = self.client.put(reverse('pathway_element_detail', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug'),
            'element_slug': plumber_element.get('slug')
        }), plumber_element, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Updated pathway element")
        updated_plumber_element = response.data

        # Teacher
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': pathway['rootElement'],
            'name': 'Teacher',
            'description': 'You can teach people things.',
            'ordering': 1,
            'alignmentUrl': "http://unit.fake.test",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        teacher_element = response.data

        """
        def test_can_update_pathway_groups(self):
        """
        group_data = {'name': 'Group of Testing', 'description': 'A group used for testing.'}
        response = self.client.post('/v2/issuers/{}/recipient-groups'.format(self.issuer.get('slug')), group_data)

        update_data = {
            'groups': [response.data.get('@id')]
        }
        response = self.client.put(
            '/v2/issuers/{}/pathways/{}'.format(self.issuer.get('slug'), pathway.get('slug')),
            update_data
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('groups')[0].get('slug'), 'group-of-testing')


@override_settings(
    CACHES=CACHE_OVERRIDE,
    CELERY_ALWAYS_EAGER=True,
    ISSUER_NOTIFY_DEFAULT=False,
    HTTP_ORIGIN="http://localhost:8000",
    JSON_ORIGIN="http://localhost:8000",
)
class PathwayCompletionTests(APITestCase, CachingTestCase):
    fixtures = ['0001_initial_superuser', 'test_badge_objects.json']

    def create_group(self):
        # Authenticate as an editor of the issuer in question
        self.client.force_authenticate(user=get_user_model().objects.get(pk=3))
        data = {'name': 'Group of Testing', 'description': 'A group used for testing.'}
        return self.client.post('/v2/issuers/edited-test-issuer/recipient-groups', data)

    def create_pathway(self, creator):
        pathway_info = {'name': 'New Path', 'description': 'A new path through learning'}
        serializer = PathwaySerializer(data=pathway_info, context={
            'issuer_slug': 'edited-test-issuer'
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=creator)
        pathway = serializer.instance

        self.assertEqual(pathway.name_hint, 'New Path')
        self.assertEqual(pathway.root_element.name, 'New Path')

        return pathway

    def create_element(self, pathway, element_info, creator):
        serializer = PathwayElementSerializer(data=element_info, context={
            'issuer_slug': 'edited-test-issuer',
            'pathway_slug': pathway.slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=creator)

        return serializer.instance

    def build_pathway(self, creator):
        pathway = self.create_pathway(creator=creator)

        element_infos = [
            {'name': 'First Element', 'description': 'Element numero uno', 'parent': pathway.slug},
            {'name': 'Second Element', 'description': 'Element numero dos', 'parent': pathway.slug},
            {'name': 'Third Element', 'description': 'Element numero tres', 'parent': pathway.slug}
        ]
        children = []
        for element_info in element_infos:
            new_element = self.create_element(pathway, element_info, creator=creator)

            requirements = {
                "junctionConfig": {
                    "requiredNumber": 1,
                    "@type": "Disjunction"
                },
                "@type": "BadgeJunction",
                "badges": [
                    OriginSetting.JSON+"/public/badges/badge-of-edited-testing"
                ]
            }

            new_element.completion_requirements = \
                CompletionRequirementSpecFactory.parse_obj(requirements).serialize()
            new_element.save()
            children.append(new_element.jsonld_id)

        root_requirements = {
            "junctionConfig": {
                "requiredNumber": 1,
                "@type": "Disjunction"
            },
            "@type": "ElementJunction",
            "elements": [
                children[0], children[1]
            ]
        }

        pathway.root_element.completion_requirements = \
            CompletionRequirementSpecFactory.parse_obj(root_requirements).serialize()
        pathway.root_element.save()
        return pathway

    def xit_test_tree_built_properly(self):
        editor = get_user_model().objects.get(pk=3)
        pathway = self.build_pathway(creator=editor)

        self.assertIsNotNone(pathway.root_element.completion_requirements)

        self.create_group()
        recipient_group = RecipientGroup.objects.first()
        member_data = {'recipient': 'testrecipient@example.com', 'name': 'Test Recipient'}
        profile, _ = RecipientProfile.cached.get_or_create(recipient_identifier=member_data['recipient'])
        membership, _ = RecipientGroupMembership.cached.get_or_create(
            recipient_group=recipient_group,
            recipient_profile=profile,
        )
        membership.name = member_data['name']
        membership.save()

        # Award a badge to recipient
        current_badgeclass = BadgeClass.objects.get(slug='badge-of-edited-testing')
        award_data = {'create_notification': False, 'recipient_identifier': member_data['recipient']}
        serializer = BadgeInstanceSerializer(data=award_data)
        serializer.is_valid(raise_exception=True)

        serializer.save(
            issuer=current_badgeclass.issuer,
            badgeclass=current_badgeclass,
            created_by=editor
        )
        badge_instance = serializer.instance

        # Check if optional element is reported in profile.cached_completions(pathway)
        completion_response = self.client.get(

            reverse('pathway_completion_detail',
                    kwargs={
                        'issuer_slug': badge_instance.issuer.slug,
                        'pathway_slug': pathway.slug,
                        'element_slug': pathway.root_element.slug
                    }) + '?recipient%5B%5D=testrecipientexamplecom'
        )

        # 'v2/issuers/{}/pathways/{}/completion/{}?recipient%5B%5D={}'.format(
        #         badge_instance.issuer.slug, pathway.slug, pathway.root_element.slug,'testrecipientexamplecom'
            #)
        # Assert that 4 elements are measured complete (root, 2 required children, 1 optional child)
        self.assertEqual(completion_response.status_code, 200)
        self.assertEqual(len(completion_response.data.get('recipientCompletions')[0]['completions']), 4)
        self.assertEqual(len(completion_response.data.get('recipients')), 1)

    def test_completion_check_when_root_requirements_null(self):
        editor = get_user_model().objects.get(pk=3)
        pathway = self.build_pathway(creator=editor)

        # null root element completion requirements
        pathway.root_element.completion_requirements = None
        pathway.root_element.save()

        self.create_group()
        recipient_group = RecipientGroup.objects.first()
        recipient = 'testrecipient2@example.com'
        profile, _ = RecipientProfile.cached.get_or_create(recipient_identifier=recipient)
        badgeclass = BadgeClass.objects.get(slug='badge-of-edited-testing')
        serializer = BadgeInstanceSerializer(data={
            'create_notification': False,
            'recipient_identifier': recipient
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(
            issuer=badgeclass.issuer,
            badgeclass=badgeclass,
            created_by=editor
        )
        badge_instance = serializer.instance

        response = self.client.get(reverse('pathway_completion_detail', kwargs={
            'issuer_slug': badge_instance.issuer.slug,
            'pathway_slug': pathway.slug,
            'element_slug': pathway.root_element.slug
        }) + '?recipient%5B%5D={}'.format(profile.slug))
        self.assertEqual(response.status_code, 200)
        recipient_completions = response.data.get('recipientCompletions', [])
        self.assertEqual(len(recipient_completions), 1)
        completions = recipient_completions[0].get('completions', [])
        # all 4 elements should be complete
        self.assertEqual(len(completions), 4)
        self.assertNotIn(False, [c.get('completed', False) for c in completions])

    def test_completion_badge_awarding(self):
        editor = get_user_model().objects.get(pk=3)
        pathway = self.build_pathway(creator=editor)
        completed_badgeclass = BadgeClass.objects.get(slug='second-badge-of-testing')
        pathway.root_element.completion_badgeclass = completed_badgeclass
        pathway.root_element.save()

        self.create_group()
        recipient_group = RecipientGroup.objects.first()
        recipient = 'testrecipient2@example.com'
        profile, _ = RecipientProfile.cached.get_or_create(recipient_identifier=recipient)

        # award badge to recipient, should complete pathway and get a completion badge
        badgeclass = BadgeClass.objects.get(slug='badge-of-edited-testing')
        serializer = BadgeInstanceSerializer(data={
            'create_notification': False,
            'recipient_identifier': recipient
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(
            issuer=badgeclass.issuer,
            badgeclass=badgeclass,
            created_by=editor
        )
        badge_instance = serializer.instance

        # get completion detail to force badge awarding
        response = self.client.get(reverse('pathway_completion_detail', kwargs={
            'issuer_slug': badge_instance.issuer.slug,
            'pathway_slug': pathway.slug,
            'element_slug': pathway.root_element.slug
        }) + '?recipient%5B%5D={}'.format(profile.slug))
        self.assertEqual(response.status_code, 200)

        # check that completion badge was awarded
        try:
            awarded = BadgeInstance.objects.get(
                badgeclass=completed_badgeclass,
                recipient_identifier=recipient
            )
        except BadgeInstance.DoesNotExist:
            self.fail("Completion Badge was not awarded")

