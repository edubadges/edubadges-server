from django.test import TestCase
import sys
import json
import os
from jsonschema import Draft4Validator

from utils import is_json, is_schemable, test_against_schema, test_against_schema_tree, test_for_errors_against_schema

# Some test assertions of different sorts
junky_assertion = {
	"uid":"100",
	"issuedOn":1395112143,
	"recipient":"sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
	"evidence":"http://someevidence.org",
	"verify":{"url":"http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100",
	"type":"hosted"},
	"badge":{
		"issuer":{ 
			"url":"http://schoolofdata.org",
			"image":"http://assets.okfn.org/p/schoolofdata/img/logo.png",
			"name":"School of Data",
			"email":"michael.bauer@okfn.org",
			"contact":"michael.bauer@okfn.org",
			"revocationList":"http://badges.schoolofdata.org/revocation",
			"description":"School of Data works to empower civil society organizations, journalists and citizens with the skills they need to use data effectively-evidence is power!",
			"_location":"http://badges.schoolofdata.org/issuer/school-of-data",
			"origin":"http://schoolofdata.org"
		},
		"description":"You have completed the Data to Diagrams module on the School of Data",
		"image":"http://p2pu.schoolofdata.org/badges/School_Of_Data_Badges/Badges/Badge_Data_to_Diagrams.png",
		"criteria":"http://badges.schoolofdata.org/badge/data-to-diagrams/criteria","name":"Data to Diagrams",
		"_location":"http://badges.schoolofdata.org/badge/data-to-diagrams"
	},
	"_originalRecipient":{
		"identity":"sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
		"type":"email",
		"hashed":True
	},
	"issued_on":1395112143
}
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




class BadgeSchemaTests(TestCase):
	def test_does_is_json_process_dicts(self):
		"""
		Make sure we can determine that a dict is not json
		"""
		someDict = { 'key': True }
		self.assertFalse(is_json(someDict))

	def test_schemable_things_should_be_schemable(self):
		"""
		Make sure that is_json will return true for a real chunk of json or a string URL
		"""
		self.assertTrue(is_schemable("http://someurl.com/badge"))
		self.assertTrue(is_schemable('{"obj": "value", "another": ["value"]}'))

	def test_does_is_json_spit_out_problems_for_unexpected_types(self):
		"""
		Make sure that is_json doesn't cause no problems if we throw some other junk at it.
		"""
		error = None
		try:
			result = is_json(list(("1", 2, "three")))
			result = is_json(set(["a", "bee", "C"]))
			result = is_json(tuple(("strings", "planes", "automobiles")))
		except:
			error = str(sys.exc_info()[0])	
		self.assertEqual(error, None)

	def test_check_schema(self):
		"""
		Make sure some schema that we're using doesn't make the validator choke. This tests them all but the
		error message spit out when there's a problem doesn't quickly tell you which schema had a problem.
		"""
		
		schemaList = ['plainuri.json','backpack-error-from-valid-1.0.json','OBI-v0.5-assertion.json','OBI-v1.0-linked-badgeclass.json']
		for schema in schemaList:
			self.assertEqual(Draft4Validator.check_schema(json.loads(open(os.path.join(os.path.dirname(__file__),'schema',schema),'r').read())), None)



	def test_against_schema_true_urlstring(self):
		"""
		Make sure that a url string returns a pass against the plainurl is_schema.
		"""
		self.assertTrue(test_against_schema('http://url.com/badgeUrl', 'plainurl'))

	def test_against_schema_tree_urlstring(self):
		"""
		Make sure that the url string is properly matched against the plainurl schema
		"""
		self.assertEqual(test_against_schema_tree("http://url.com/badgeUrl"), 'plainurl')

	def test_against_schema_backpack_error_assertion(self):
		"""
		Make sure a junky ol' backpack-mangled badge gets matched with the proper schema
		"""

		self.assertTrue(test_against_schema(junky_assertion, 'backpack_error_1_0'))
		self.assertFalse(test_against_schema(junky_assertion, 'v1_0strict'))

	def test_junky_tree(self):
		"""
		Make sure a junky ol' backpack-mangled badge gets matched with the proper is_schemable
		"""

		self.assertEqual(test_against_schema_tree(junky_assertion), 'backpack_error_1_0')

	def test_valid_1_0_tree(self):
		"""
		Make sure a valid 1.0 assertion makes its way through the tree
		"""
		self.assertEqual(test_against_schema_tree(valid_1_0_assertion), 'v1_0strict')



class BadgeContextTests(TestCase):
	def nothing(self):
		return

