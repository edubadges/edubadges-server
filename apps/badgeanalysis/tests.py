from django.test import TestCase
import sys
import json
import os
from jsonschema import Draft4Validator
import pngutils

import utils
from badgeanalysis.scheme_models import BadgeScheme, BadgeSchemaValidator
from badgeanalysis.models import OpenBadge
from badgeanalysis.badge_objects import Assertion, BadgeClass, IssuerOrg, Extension, BadgeObject, badge_object_class
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.cur_context import current_context


# Construct a docloader function that will return preloaded responses for predetermined URLs
# Load in a dict of urls and the response bodies you want them to deliver:
# response_list = {'http://google.com': 'Hacked by the lizard overlords, hahaha!'}
def mock_docloader_factory(response_list):
    def mock_docloader(url):
        return response_list[url]
    return mock_docloader


class BadgeUtilsTests(TestCase):
    def test_does_is_json_process_dicts(self):
        """
        Make sure we can determine that a dict is not json
        """
        someDict = {'key': True}
        self.assertFalse(utils.is_json(someDict))

    def test_try_json_load_good(self):
        self.assertEqual(utils.try_json_load('{ "key": 42 }'), {'key': 42})

    def test_try_json_load_already_obj(self):
        self.assertEqual(utils.try_json_load({'key': 42}), {'key': 42})

    def test_try_json_load_junk(self):
        self.assertEqual(utils.try_json_load("{ holey guacamole batman"), "{ holey guacamole batman")
        self.assertEqual(utils.try_json_load(23311233), 23311233)

    def test_schemable_things_should_be_schemable(self):
        """
        Make sure that is_json will return true for a real chunk of json or a string URL
        """
        self.assertTrue(utils.is_schemable("http://someurl.com/badge"))
        self.assertTrue(utils.is_schemable('{"obj": "value", "another": ["value"]}'))

    def test_does_is_json_spit_out_problems_for_unexpected_types(self):
        """
        Make sure that is_json doesn't cause no problems if we throw some other junk at it.
        """

        try:
            utils.is_json(list(("1", 2, "three")))
            utils.is_json(set(["a", "bee", "C"]))
            utils.is_json(tuple(("strings", "planes", "automobiles")))
        except:
            error = str(sys.exc_info()[0])
        else:
            error = None
        finally:
            self.assertEqual(error, None)


class BadgeSchemaTests(TestCase):
    fixtures = ['0001_initial_superuser','0002_initial_schemes_and_validators']

    # def test_check_schema(self):
    #   """
    #   Make sure some schema that we're using doesn't make the validator choke. This tests them all but the
    #   error message spit out when there's a problem doesn't quickly tell you which schema had a problem.
    #   """

    #   schemaList = ['plainuri.json','backpack-error-from-valid-1.0.json','OBI-v0.5-assertion.json','OBI-v1.0-linked-badgeclass.json']
    #   for schema in schemaList:
    #       self.assertEqual(Draft4Validator.check_schema(json.loads(open(os.path.join(os.path.dirname(__file__),'schema',schema),'r').read())), None)
    def test_achievery_assertion_for_schema_match(self):
        # "issuedOn": "2014-09-05T21:45:09.000Z",
        assertion = """{
            "recipient": "sha256$1a29bbe7d65355ce7647793396041c7bebbe333e677222c5ca116f5cc038b9ef",
            "verify": {
                "type": "hosted",
                "url": "http://app.achievery.com/badge-assertion/4613"
            },
            "uid": "4613",
            "issuedOn": "2014-09-05",
            "expires": null,
            "badge": {
                "name": "DPD Project Contributor",
                "description": "Awarded for team members on the DPD project that studied badge system design from 2012-2014.",
                "image": "https://images.achievery.com/badgeImages/DPDContributorBadge_1716_1.png",
                "tags": [
                    "Higher Education",
                    "Writing"
                ],
                "issuer": {
                    "name": "Design Principles Documentation Project",
                    "image": "https://images.achievery.com/organization/badger-icon-transparent.png",
                    "url": "http://app.achievery.com/passport/id/2515",
                    "_location": "http://app.achievery.com/badge-issuer/1716",
                    "origin": "http://app.achievery.com"
                },
                "criteria": "http://app.achievery.com/badge/1716",
                "alignment": [
                    {
                        "name": "DPD Project Website",
                        "url": "http://dpdproject.info",
                        "description": "The homepage for the DPD Project showcases design principles for using digital badges for learning, related research literature, analysis of common challenges, and badge system design tools developed by the team."
                    }
                ],
                "_location": "http://app.achievery.com/badge-class/1716"
            },
            "evidence": "http://app.achievery.com/badge-earned/4613",
            "image": "https://images.achievery.com/badgeImages/DPDContributorBadge_1716_1.png",
            "_originalRecipient": {
                "type": "email",
                "hashed": true,
                "salt": "2zjIsSSl12PiZJkiq4Hq33ImLFhHMBHBrSzDyc9DiOtGVg8P7VDVPNa2QgAXHQQ9",
                "identity": "sha256$1a29bbe7d65355ce7647793396041c7bebbe333e677222c5ca116f5cc038b9ef"
            },
            "salt": "2zjIsSSl12PiZJkiq4Hq33ImLFhHMBHBrSzDyc9DiOtGVg8P7VDVPNa2QgAXHQQ9",
            "issued_on": "2014-09-05T21:45:09.000Z"
        }"""
        schema_json = BadgeSchemaValidator.objects.get(pk=2).schema_json
        self.assertEqual(BadgeScheme.test_against_schema_verbose(json.loads(assertion), schema_json), "None is not valid under any of the given schemas\n\nFailed validating u'anyOf' in schema[u'properties'][u'expires']:\n    {u'anyOf': [{u'$ref': u'#/definitions/ISODateTime'},\n                {u'$ref': u'#/definitions/UNIXTimeStamp'}]}\n\nOn instance[u'expires']:\n    None")

    def test_against_schema_true_urlstring(self):
        """
        Make sure that a url string returns a pass against the plainurl is_schema.
        """
        # self.assertTrue(test_against_schema('http://url.com/badgeUrl', 'plainurl'))
        # self.assertFalse(test_against_schema("a stinkin' turnip", 'plainurl'))
        # self.assertFalse(test_against_schema("", 'plainurl'))

    def test_against_schema_tree_urlstring(self):
        """
        Make sure that the url string is properly matched against the plainurl schema
        """
        # self.assertEqual(test_against_schema_tree("http://url.com/badgeUrl"), 'plainurl')

    def test_against_schema_backpack_error_assertion(self):
        """
        Make sure a junky ol' backpack-mangled badge gets matched with the proper schema
        """

        # self.assertTrue(test_against_schema(junky_assertion, 'backpack_error_1_0'))
        # self.assertFalse(test_against_schema(junky_assertion, 'v1_0strict'))

    def test_junky_tree(self):
        """
        Make sure a junky ol' backpack-mangled badge gets matched with the proper is_schemable
        """

        # self.assertEqual(test_against_schema_tree(junky_assertion), 'backpack_error_1_0')

    def test_valid_1_0_tree(self):
        """
        Make sure a valid 1.0 assertion makes its way through the tree
        """
        # self.assertEqual(test_against_schema_tree(valid_1_0_assertion), 'v1_0strict')

    def test_schema_context(self):
        # self.assertEqual( schema_context('v1_0strict'), 'http://standard.openbadges.org/1.0/context' )
        pass


class BadgeContextTests(TestCase):
    def test_has_context(self):
        self.assertTrue(utils.has_context({"@context": "http://someurl.com/context", "someprop": 42}))
        self.assertFalse(utils.has_context({"howdy": "stranger"}))

    def test_has_context_handle_nonObjects(self):
        """
        This test isn't working right, but it's supposed to make sure has_context doesn't choke on things.
        """
        exceptage = None
        try:
            self.assertFalse(utils.has_context("Hahaha, I'm a string."))
            self.assertFalse(utils.has_context([{"@context": "http://someurl.com/context"}]))
        except AssertionError as e:
            exceptage = e
        finally:
            self.assertEqual(exceptage, None)

# Some test assertions of different sorts
junky_assertion = {
    "uid": "100",
    "issuedOn": 1395112143,
    "recipient": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
    "evidence": "http://someevidence.org",
    "verify": {
        "url": "http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100",
        "type": "hosted"
    },
    "badge": {
        "issuer": {
            "url": "http://schoolofdata.org",
            "image": "http://assets.okfn.org/p/schoolofdata/img/logo.png",
            "name": "School of Data",
            "email": "michael.bauer@okfn.org",
            "contact": "michael.bauer@okfn.org",
            "revocationList": "http://badges.schoolofdata.org/revocation",
            "description": "School of Data works to empower civil society organizations, journalists and citizens with the skills they need to use data effectively-evidence is power!",
            "_location": "http://badges.schoolofdata.org/issuer/school-of-data",
            "origin": "http://schoolofdata.org"
        },
        "description": "You have completed the Data to Diagrams module on the School of Data",
        "image": "http://p2pu.schoolofdata.org/badges/School_Of_Data_Badges/Badges/Badge_Data_to_Diagrams.png",
        "criteria": "http://badges.schoolofdata.org/badge/data-to-diagrams/criteria",
        "name": "Data to Diagrams",
        "_location": "http://badges.schoolofdata.org/badge/data-to-diagrams"
    },
    "_originalRecipient": {
        "identity": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
        "type": "email",
        "hashed": True
    },
    "issued_on": 1395112143
}
junky_original_assertion = {
    "evidence": "http://someevidence.org",
    "recipient": {
        "hashed": True,
        "identity": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
        "type": "email"
    },
    "uid": "100",
    "badge": "http://badges.schoolofdata.org/badge/data-to-diagrams",
    "verify": {
        "url": "http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100",
        "type": "hosted"
    },
    "issuedOn": 1395112143
}
junky_badgeclass = {
    "criteria": "http://badges.schoolofdata.org/badge/data-to-diagrams/criteria",
    "issuer": "http://badges.schoolofdata.org/issuer/school-of-data",
    "description": "You have completed the \"Data to Diagrams\" module on the School of Data",
    "name": "Data to Diagrams",
    "image": "http://p2pu.schoolofdata.org/badges/School_Of_Data_Badges/Badges/Badge_Data_to_Diagrams.png"
}
junky_issuer = {
    "description": "School of Data works to empower civil society organizations",
    "image": "http://assets.okfn.org/p/schoolofdata/img/logo.png",
    "revocationList": "http://badges.schoolofdata.org/revocation",
    "contact": "michael.bauer@okfn.org", "email": "michael.bauer@okfn.org",
    "url": "http://schoolofdata.org",
    "name": "School of Data"
}
junky_docloader = mock_docloader_factory(
    {
        'http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100': junky_original_assertion,
        'http://badges.schoolofdata.org/badge/data-to-diagrams': junky_badgeclass,
        'http://badges.schoolofdata.org/issuer/school-of-data': junky_issuer
    }
)

valid_1_0_assertion = {
    "uid": "2f900c7c-f473-4bff-8173-71b57472a97f",
    "recipient": {
        "identity": "sha256$1665bc8985e802067453647c1676b07a1834c327bfea24c67f3dbb721eb84d22",
        "type": "email",
        "hashed": True,
        "salt": "UYMA1ybJ4UfqHJO4r3x7LjpGE0LEog"
    },
    "badge": "http://openbadges.oregonbadgealliance.org/api/badges/53d727a11f04f3a84a99b002",
    "verify": {
        "type": "hosted",
        "url": "http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205"
    },
    "issuedOn": 1406747839,
    "image": "http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205/image"
}
valid_1_0_badgeclass = {
    "_id": {"$oid": "53d727a11f04f3a84a99b002"},
    "name": "Oregon Open Badges Working Group Initial Meeting",
    "description": "Invited participant to the first meeting of Oregon's Open Badges Working Group in July 2014.",
    "image": "http://placekitten.com/300/300",
    "criteria": "http://openbadges.oregonbadgealliance.org/assets/criteria/obwg-initial-meeting.html",
    "issuer": "http://openbadges.oregonbadgealliance.org/api/issuers/53d41603f93ae94a733ae554",
    "tags": ["participation"]
}
valid_1_0_issuer = {
    "_id": {"$oid": "53d41603f93ae94a733ae554"},
    "name": "Oregon Badge Alliance",
    "url": "http://oregonbadgealliance.org",
    "description": "The Oregon Badge Alliance serves as a focal point for collaborations between state institutions, employers, and the education community as we work together to build a vibrant ecosystem for badges and micro-certifications in Oregon.",
    "email": "oregonbadgealliance@gmail.com",
    "fullyQualifiedUrl": "http://openbadges.oregonbadgealliance.org/api/issuers/53d41603f93ae94a733ae554"
}
valid_1_0_docloader = mock_docloader_factory(
    {
        'http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205': valid_1_0_assertion,
        'http://openbadges.oregonbadgealliance.org/api/badges/53d727a11f04f3a84a99b002': valid_1_0_badgeclass,
        'http://openbadges.oregonbadgealliance.org/api/issuers/53d41603f93ae94a733ae554': valid_1_0_issuer,
        'http://standard.openbadges.org/1.0/context.json': { 'document': current_context(), 'contextUrl': None, 'documentUrl': 'http://standard.openbadges.org/1.0/context.json' }
    }
)

simpleOneOne = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "http://example.org/assertion25",
    "uid": '25',
    "recipient": {
        "identity": "testuser@example.org",
        "type": "email",
        "hashed": False
    },
    "badge": "http://example.org/badge1",
    "verify": {
        "type": "hosted",
        "url": "http://example.org/assertion25"
    },
    "issuedOn": "2014-01-31"
}
simpleOneOneTwo = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "http://example.org/assertion30",
    "uid": '30',
    "recipient": {
        "identity": "testuser@example.org",
        "type": "email",
        "hashed": False
    },
    "badge": "http://example.org/badge1",
    "verify": {
        "type": "hosted",
        "url": "http://example.org/assertion25"
    },
    "issuedOn": "2014-01-31"
}
simpleOneOneBC = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "badgeclass",
    "@id": "http://example.org/badge1",
    "name": "Badge of Awesome",
    "description": "Awesomest badge for awesome people.",
    "image": "http://placekitten.com/300/300",
    "criteria": "http://example.org/badge1criteria",
    "issuer": "http://example.org/issuer"
}
simpleOneOneIssuer = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "issuerorg",
    "@id": "http://example.org/issuer",
    "name": "Issuer of Awesome",
    "url": "http://example.org"
}
oneone_docloader = mock_docloader_factory(
    {
        'http://example.org/assertion25': simpleOneOne,
        'http://example.org/assertion30': simpleOneOneTwo,
        'http://example.org/badge1': simpleOneOneBC,
        'http://example.org/issuer': simpleOneOneIssuer,
        # Gotta duplicate the function of the original pyld docloader here
        'http://standard.openbadges.org/1.1/context.json': { 'document': current_context(), 'contextUrl': None, 'documentUrl': 'http://standard.openbadges.org/1.1/context.json' }
    }
)

oneOneArrayType = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": ["assertion", "http://othertype.com/type"],
    "@id": "http://example.org/assertion25",
    "uid": '25'
}

oneOneNonUrlID = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "assertion25",
    "uid": '25'
}
simpleOneOneNoId = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "verify": {"type": "hosted", "url": "http://example.org/assertion25"},
    "uid": '25'
}


class OpenBadgeTests(TestCase):
    fixtures = ['0001_initial_superuser','0002_initial_schemes_and_validators']

    # def test_save_badge_with_custom_docloader(self):
    #     badge = OpenBadge(badge_input=simpleOneOne, recipient_input='testuser@example.org')
    #     badge.save(**{'docloader': oneone_docloader})
    #     self.assertTrue(badge.pk is not None)

#     def test_simple_OpenBadge_construction_noErrors(self):
#         try:
#             openBadge = OpenBadge(simpleOneOne)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getProp('assertion', 'uid'), 25)
#         self.assertEqual(openBadge.getProp('assertion', '@type'), 'assertion')

#     def test_oneOneArrayType(self):
#         try:
#             openBadge = OpenBadge(oneOneArrayType)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getProp('assertion', 'uid'), 25)

#     def test_oneOneNonUrlID(self):
#         #TODO, both implement id validation and then make this test actually pass
#         try:
#             openBadge = OpenBadge(oneOneNonUrlID)
#         except Exception as e:
#             # What is this doing?
#             self.assertFalse(e is None)
#         self.assertEqual(openBadge.getProp('assertion', 'uid'), 25)

#     def test_id_from_verify_url(self):
#         try:
#             openBadge = OpenBadge(simpleOneOne)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getProp('assertion', '@id'), "http://example.org/assertion25")

#     def test_valid_1_0_construction(self):
#         try:
#             openBadge = OpenBadge(valid_1_0_assertion)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getProp('assertion', '@type'), 'assertion')
#         self.assertEqual(openBadge.getProp('assertion', '@id'), 'http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205')
#         self.assertEqual(openBadge.getProp('assertion', 'issuedOn'), 1406747839)

#     def test_junky_construction(self):
#         try:
#             openBadge = OpenBadge(junky_assertion)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getProp('assertion', '@type'), 'assertion')
#         self.assertEqual(openBadge.getProp('assertion', '@id'), 'http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100')
#         self.assertEqual(openBadge.getProp('assertion', 'issuedOn'), 1395112143)

#     def test_getting_prop_by_iri_simpleOneOne(self):
#         try:
#             openBadge = OpenBadge(simpleOneOne)
#         except Exception as e:
#             self.assertEqual(e, None)
#         self.assertEqual(openBadge.getLdProp('assertion', 'http://standard.openbadges.org/definitions#AssertionUid'), 25)
#         self.assertEqual(openBadge.getLdProp('assertion', 'http://standard.openbadges.org/definitions#BadgeClass'), "http://example.org/badge1")


class ImageExtractionTests(TestCase):
    def test_basic_image_extract(self):
        imgFile = open(os.path.join(os.path.dirname(__file__), 'testfiles', '1.png'), 'r')
        assertion = pngutils.extract(imgFile)
        self.assertTrue(utils.is_json(assertion))

#         assertion = utils.try_json_load(assertion)
#         self.assertEqual(assertion.get("uid"), "2f900c7c-f473-4bff-8173-71b57472a97f")

#     def test_analyze_image_upload(self):
#         imgFile = open(os.path.join(os.path.dirname(__file__), 'testfiles', '1.png'), 'r')

#         openBadge = utils.analyze_image_upload(imgFile)
#         self.assertEqual(openBadge.getProp("assertion", "uid"), "2f900c7c-f473-4bff-8173-71b57472a97f")


class BadgeObjectsTests(TestCase):
    fixtures = ['0001_initial_superuser', '0002_initial_schemes_and_validators']

    def test_badge_object_class(self):
        self.assertEqual(badge_object_class('assertion'), Assertion)

    def test_mock_docloader_factory(self):
        response_list = {'http://google.com': 'Hahahaha, hacked by the lizard overlords.'}
        docloader = mock_docloader_factory(response_list)
        self.assertEqual(docloader('http://google.com'), 'Hahahaha, hacked by the lizard overlords.')

    # def test_assertion_processing_oneone(self):
    #     self.maxDiff = None
    #     badgeMetaObject = badge_object_class('assertion').processBadgeObject(
    #         {'badgeObject': simpleOneOne},
    #         oneone_docloader
    #         )
    #     expected_result = {'notes': ['<RecipientRequiredValidator: Recipient input not needed, embedded recipient identity is not hashed>']}
    #     self.assertEqual(str(badgeMetaObject.get('notes', [0])[0]), expected_result['notes'][0])

    # def test_assertion_processing_valid_1_0_with_identifier(self):
    #     self.maxDiff = None
    #     # import pdb; pdb.set_trace();
    #     b = Assertion(iri='http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205')
    #     b.save(**{'docloader': valid_1_0_docloader})
    #     self.assertEqual(b.badgeclass.iri, 'http://openbadges.oregonbadgealliance.org/api/badges/53d727a11f04f3a84a99b002')

    def test_assertion_badge_assertion_create_oneone(self):
        bb = Assertion(iri='http://example.org/assertion25', badge_object={'uid':"toooooooooots"})
        bb.save(**{'docloader': oneone_docloader})
        self.assertTrue(isinstance(bb.badgeclass, BadgeClass))
        self.assertTrue(isinstance(bb.badgeclass.issuerorg, IssuerOrg))

    def test_assertion_badge_assertion_get_or_create_oneone(self):
        bb = Assertion.get_or_create_by_iri('http://example.org/assertion25', **{'docloader': oneone_docloader})
        self.assertTrue(isinstance(bb.badgeclass, BadgeClass))
        self.assertTrue(isinstance(bb.badgeclass.issuerorg, IssuerOrg))

    def test_multiple_assertion_same_badgeclass_oneone(self):
        bb = Assertion(iri='http://example.org/assertion25')
        bb.save(**{'docloader': oneone_docloader})

        cc = Assertion(iri='http://example.org/assertion30')
        cc.save(**{'docloader': oneone_docloader})

        self.assertEqual(bb.badgeclass.pk, cc.badgeclass.pk)

    # def create_via_OpenBadge_oneone(self):
        # b = OpenBadge(badge_input='http://example.org/assertion25', recipient_input='testuser@example.org')
        # b.save(**{docloader: simple_oneone_docloader})
        # self.assertTrue(isinstance(Assertion.objects.get(iri='http://example.org/assertion25'), Assertion))


class OpenBadgeIntegrationTests(TestCase):
    fixtures = ['0001_initial_superuser', '0002_initial_schemes_and_validators']

    # def test_successful_OpenBadge_save(self):
    #     badge_input = valid_1_0_assertion
    #     recipient_input = 'nate@ottonomy.net'
    #     b = OpenBadge(badge_input=badge_input, recipient_input=recipient_input)
    #     try:
    #         b.save(**{'docloader': valid_1_0_docloader})
    #     except Exception as e:
    #         self.assertEqual(e, None)
    #     else:
    #         self.assertTrue(True) # Yay, no errors!

    # def test_OpenBadge_save_bad_recipient(self):
    #     badge_input = valid_1_0_assertion
    #     recipient_input = 'nate@ottonomy.newt'
    #     b = OpenBadge(badge_input=badge_input, recipient_input=recipient_input)
    #     try:
    #         b.save(**{'docloader': valid_1_0_docloader})
    #     except Exception as e:
    #         self.assertTrue(isinstance(e, BadgeValidationError))
    #         self.assertEqual(e.to_dict()['validator'], 'Functional:AssertionRecipientValidator')
    #     else: 
    #         self.assertTrue(False) # Boo, there should have been an error!
