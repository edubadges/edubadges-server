"""
Utilities to deal with understanding badges from an unspecified issuer
"""
import json
from jsonschema import validate, Draft4Validator, draft4_format_checker
from jsonschema.exceptions import FormatError, ValidationError
import os
import re
from pyld import jsonld
import pngutils
from cur_context import current_context


"""
Loading files from system
"""
schemaFiles = {}
def load_schema_from_filesystem(filename):
    """
    Loads a schema from the file system from a short filename
    TODO: replace with a database-stored model for schemes, context and schema
    """
    if not filename in schemaFiles:
        schemaFiles[filename] = json.loads(open(os.path.join(os.path.dirname(__file__),'schema',filename),'r').read())
    return schemaFiles[filename]

contextFiles = {}
def load_context_from_filesystem(filename):
    """
    Loads a context from the file system based on the filename specified
    TODO: replace with a database-stored model for schemes, context and schema
    """
    if not filename in contextFiles:
        contextFiles[filename] = json.loads(open(os.path.join(os.path.dirname(__file__),'context',filename),'r').read())
    return contextFiles[filename]



def verify_recipient(identifier, hash_string, salt):
    """
    Check if a badge recipient is indeed the expected recipient (email address)
    """
    if hash_string.startswith('sha256$'):
        return hash_string == 'sha256$' + hashlib.sha256(email+salt).hexdigest()
    elif hash_string.startswith('md5$'):
        return hash_string == 'md5$' + hashlib.md5(email+salt).hexdigest()


def is_json(string):
    if isinstance(string, dict):
        return False
    try:
        json_result = json.loads(string)
    except ValueError, e:
        return False
    except TypeError, e:
        return False
    else: 
        return True

def try_json_load(input):
    if isinstance(input, dict) or isinstance(input, (int, long, float, complex)):
        return input
    if isinstance(input, (str, unicode)):
        try:
            json_result = json.loads(input)
        except ValueError as e:
            return input
        except TypeError as e:
            return input
        else:
            return json_result

def test_probable_url(string):
    earl = re.compile(r'^(https?|ftp)://[^\s/$.?#].[^\s]*$')
    if isinstance(string, (str,unicode)) and earl.match(string):
        return True
    else:
        return False



"""
Utilities for matching badge objects with schema
""" 
def is_schemable(input):
    if is_json(input) or isinstance(input, list) or isinstance(input, (str, unicode)):
        return True
    else:
        return False



"""
Utilities for JSON-LD + badge objects
"""
def has_context(badgeObject):
    context = None
    try:
        context = badgeObject.get('@context')
    except AttributeError:
        return False
    finally:
        if context:
            return True
        return False

# TODO: This approach will not be able to handle issuers who redirect to an OBI context.
def validateMainContext(contextInput):
    url = re.compile(r"standard\.openbadges\.org/[\d\.]+/context$")
    if isinstance(contextInput, str) and url.search(contextInput):
        return contextInput
    elif isinstance(contextInput, list):
        for contextElement in contextInput:
            if validateMainContext(contextElement):
                return contextElement
    elif isinstance(contextInput, dict):
        # no need to accept these for now
        pass
    return None


# Gets a simple string (compact IRI in the OBI context of the OBI object type)
def validateObiType(typeInput):
    #TODO rework this with JSON-LD compaction instead of a simple in set operation. Gotta handle full IRIs

    if isinstance(typeInput, str) and typeInput in ('assertion', 'badgeclass', 'issuerorg'):
        return typeInput

    elif isinstance(typeInput, list):
        for typeElement in typeInput:
            elType = validateObiType(typeElement)
            if elType is not None:
                return elType
    return None


def validateId(idString):
    if test_probable_url(idString):
        return idString
    return None


def extract_assertion_from_image(imageFile):
    return pngutils.extract(imageFile)


def is_image_data_uri(imageString):
    dataRe = re.compile(r'^data:', flags=re.I)
    if dataRe.match(imageString):
        return True
    else:
        return False


def fetch_linked_component(url, documentLoader=None):
    """
    Unless overridden, this uses the PyLD package document loader,
    which returns a loaded document in a wrapper object.
    {
        'document': (The document we wanted)
        'documentUrl': the input url
        'contextUrl': context link if provided in a link header from the http request.
    }
    """
    if documentLoader:
        loadDoc = documentLoader
    else:
        loadDoc = jsonld.load_document

    try:
        result = loadDoc(url)
        result = result['document']

    except (jsonld.JsonLdError, Exception) as e:
        raise IOError("error loading document " + url + " " + e)
        return None
    else:
        return result


def get_iri_for_prop_in_current_context(shortProp):
    vessel = {
        '@context': current_context(),
    }
    vessel[shortProp] = "TEMPVALUE, McDAWG!"
    crunk_cup = jsonld.expand(vessel)
    if isinstance(crunk_cup, list):
        return crunk_cup[0].keys()[0]

def image_upload_to():
    return 'uploads/badges/received'

def baker_api_url(assertion_url):
    # TODO: build this service internally.
    return "http://backpack.openbadges.org/baker?assertion=" + assertion_url
