"""
Utilities to deal with understanding badges from an unspecified issuer
"""
import json
from jsonschema import validate, Draft4Validator, FormatChecker
from jsonschema.exceptions import FormatError, ValidationError
import os


SCHEMA_KEYS= {
	'plainurl': {
		'schemaFile': 'plainuri.json',
	},
	'v0_5': {
		'schemaFile': 'OBI-v0.5-assertion.json',
		'type': 'http://openbadges.org/standard#assertion0.5',
		'context': 'http://openbadges.org/standard/context/0.5'
	},
	'v1_0strict': {
		'schemaFile': 'OBI-v1.0-linked-badgeclass.json',
		'type': 'http://openbadges.org/standard#assertionJunky0.5',
		'context': 'http://openbadges.org/standard/context/junky0.5'
	},
	'backpack_error_1_0': {
		'schemaFile': 'backpack-error-from-valid-1.0.json',
		'type': 'http://openbadges.org/standard#assertion1.0',
		'context': 'http://openbadges.org/standard/context/1.0'
	}
}
schemaFiles = {}

SCHEMA_TREE = {
	'test': 'plainurl',
	'noMatch': {
		'test': 'backpack_error_1_0',
		'noMatch': { 
			'test': 'v1_0strict',
			'noMatch': {
				'test': 'v0_5'
			}
		}
	}
}

def schema_filename(schemaKey):
	return SCHEMA_KEYS[schemaKey]['schemaFile']
def schema_type(schemaKey):
	return SCHEMA_KEYS[schemaKey]['type']
def schema_context(schemaKey):
	return SCHEMA_KEYS[schemaKey]['context']

def load_schema_from_filesystem(schemaKey):
	"""
	TODO: Implement
	"""
	if not schemaKey in schemaFiles:
		schemaFiles[schemaKey] = json.loads(open(os.path.join(os.path.dirname(__file__),'schema',schema_filename(schemaKey)),'r').read())
	return schemaFiles[schemaKey]
	 

def verify_recipient(identifier, hash_string, salt):
	"""
	Check if a badge recipient is indeed the expected recipient (email address)
	"""
	if hash_string.startswith('sha256$'):
		return hash_string == 'sha256$' + hashlib.sha256(email+salt).hexdigest()
	elif hash_string.startswith('md5$'):
		return hash_string == 'md5$' + hashlib.md5(email+salt).hexdigest()


def fetch_linked_badge_object(url):
	""" 
	TODO: Implement 
	"""
	return ''


def is_json(str):
	if isinstance(str, dict):
		return False
	try:
		json_result = json.loads(str)
	except ValueError, e:
		return False
	except TypeError, e:
		return False
	else: 
		return True


def is_schemable(input):
	if is_json(input) or isinstance(input, list) or isinstance(input, str):
		return True
	else:
		return False


def analyze_badge_object(badgeInput):
	if isinstance(badgeInput, dict): 
		badgeObject = json.dumps(badgeObject)
	else: 
		badgeObject = badgeInput

	if is_json(badgeObject):
		schemaMatch = test_against_schema(SCHEMA_TREE,badgeObject)
	return None


def test_against_schema_tree(badgeObject, testTree=SCHEMA_TREE):
	if 'test' in testTree:
		schemaKey = testTree['test']
	else: 
		raise LookupError("Schema Tree malformed, could not find a test reference when needed. " + str(testTree))
		return None

	if test_against_schema(badgeObject, schemaKey):
		if 'match' in testTree:
			return test_against_schema_tree(badgeObject, testTree['match'])
		else: 
			return schemaKey
	elif 'noMatch' in testTree:
		return test_against_schema_tree(badgeObject, testTree['noMatch'])
	else:
		return None

def test_against_schema(badgeObject, schemaKey):
	"""
	Reads the specified schema based on the filename registered for schemaKey, and processes it into an object with json.loads()
	Then validates the badge object against it.
	"""
	v = test_for_errors_against_schema(badgeObject, schemaKey)
	if isinstance(v,ValidationError):
		return False
	else:
		return True

def test_for_errors_against_schema(badgeObject, schemaKey):
	currentSchema = load_schema_from_filesystem(schemaKey)
	try:
		validate(badgeObject, currentSchema, Draft4Validator, format_checker=FormatChecker())
	except ValidationError as e:
		return e
	else: 
		return None


