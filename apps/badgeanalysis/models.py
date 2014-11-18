from django.db import models
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import reverse
import re
from pyld import jsonld
import json

from jsonschema import validate, Draft4Validator, draft4_format_checker
from jsonschema.exceptions import FormatError, ValidationError

import basic_models
from djangosphinx.models import SphinxSearch
from jsonfield import JSONField

import badgeanalysis.utils


class BadgeScheme(basic_models.SlugModel):
	default_type = models.CharField(max_length=64)
	context_url = models.URLField(verbose_name='URL location of the JSON-LD context file core to this scheme', max_length=2048)
	description = models.TextField(blank=True)
	context_json = JSONField(blank=True)

	def get_form(self):
		from badges.forms import BadgeSchemeForm
		return BadgeSchemeForm(instance=self)

	def registerValidators(self):
		# TODO: Use JSON-LD for this?
		contextObj = json.loads(self.context_json)
		#import pdb; pdb.set_trace();
		validators = contextObj.get('obi:validation')
		if validators is not None and isinstance(validators, list):
			for validator in validators:
				validationSchema = validator.get('obi:validationSchema')
				validatesType = validator.get('obi:validatesType')
				schema_json = json.loads(badgeanalysis.utils.fetch_linked_component(validationSchema))
				
				bsv = BadgeSchemaValidator(validation_schema=validationSchema, validates_type=validatesType, schema_json=schema_json, scheme=self)
				
				bsv.save()
		elif isinstance(validators, dict):
			bsv = BadgeSchemaValidator(self, validation_schema=validators.get('obi:validationSchema'), validates_type=validators.get('obi:validatesType'), scheme=self)
			bsv.save()

	def save(self, *args, **kwargs): 
		if not self.pk:
			if self.context_json is None:
				self.context_json = badgeanalysis.utils.fetch_linked_component(self.context_url)

			super(BadgeScheme, self).save(*args, **kwargs)

			self.registerValidators()
		

		else:
			super(BadgeScheme, self).save(*args, **kwargs)

	def get_absolute_url(self):
		return reverse('badgescheme_detail', args=[self.slug])

	@classmethod
	def get_context_file_by_url(cls, url):
		try:
			result = cls.objects.get(context_url=url)
		except MultipleObjectsReturned as e:
			raise e
		except ObjectDoesNotExist:
			return None
		else: 
			return result.context_json

	@classmethod
	def get_legacy_scheme_match(cls, badgeObject, badgeObjectType):
		LEGACY_SLUGS = ['0_5_assertion', 'backpack_error', '1_0_strict']
		VALID_TYPES = ['assertion', 'badgeclass', 'issuerorg']

		if not badgeObjectType in VALID_TYPES:
			raise TypeError("Input type " + badgeObjectType + " isn't one of the valid options.")

		schemes = cls.objects.filter(slug__in=LEGACY_SLUGS).prefetch_related('schemes')

		# Here's the first schema_json:
		schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].schema_json

		# heres the type one validates: 
		schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].validates_type

		# build a dict of schema_json that match our type
		schemaTree = {}
		schemaTree['assertion'] = {
			'test': '0_5_assertion',
			'noMatch': {
				'test': 'backpack_error',
				'noMatch': { 
					'test': '1_0strict'
				}
			}
		}
		schemaTree['badgeclass'] = {
			'test': '1_0strict'
		}
		schemaTree['issuerorg'] = {
			'test': '1_0strict'
		}
		
		def insert_into_tree(schemaSlug, contextUrl, schemaJson, tree=schemaTree[badgeObjectType]):
			if tree['test'] == schemaSlug:
				tree['context_url'] = contextUrl
				tree['schema_json'] = schemaJson
				return tree
			elif tree['noMatch']: 
				return insert_into_tree(schemaSlug, contextUrl, schemaJson, tree['noMatch'])



		for scheme in schemes:
			currentSchemaJson = None
			for validator in scheme._prefetched_objects_cache['schemes']._result_cache:
				if validator.validates_type == badgeObjectType:
					currentSchemaJson = validator.schema_json

			if insert_into_tree(scheme.slug, scheme.context_url, currentSchemaJson) is None:
				raise LookupError("Could not insert schema json for " + scheme.slug + " into tree")

		try:
			slugMatch = cls.test_against_schema_tree(badgeObject, schemaTree[badgeObjectType])
		except LookupError as e:
			raise e

		if slugMatch:
			return {
				"context_url": slugMatch['context_url'],
				"type": badgeObjectType,
				"schemeSlug": slugMatch['test']
			}
		else:
			return None


		def test_against_schema_tree(cls, badgeObject, testTree):
			if not 'test' in testTree:
				raise LookupError("Schema Tree malformed, could not find a test reference when needed. " + str(testTree))
				return None

			if cls.test_against_schema(badgeObject, testTree['schema_json']):
				# There are only more tests down the noMatch path, so we can return right here.
				return testTree
			elif 'noMatch' in testTree:
				return test_against_schema_tree(badgeObject, testTree['noMatch'])
			else:
				return None


		def test_against_schema(cls, badgeObject, schemaJson):
			"""
			Reads the specified schema based on the filename registered for schemaKey, and processes it into an object with json.loads()
			Then validates the badge object against it.
			"""
			try:
				validate(badgeObject, schemaJson, Draft4Validator, format_checker=draft4_format_checker)
			except ValidationError as e:
				return False
			else:
				return True




class BadgeSchemaValidator(basic_models.DefaultModel):
	scheme = models.ForeignKey(BadgeScheme, related_name='schemes')
	validates_type = models.CharField(max_length=2048)
	validation_schema = models.URLField(verbose_name='URL location of the validation schema', max_length=2048)
	schema_json = JSONField(blank=True)
	
	def save(self, *args, **kwargs):
		if not self.pk:
			
			try:
				result = BadgeSchemaValidator.objects.get(validation_schema=self.validation_schema)
			except MultipleObjectsReturned:
				pass
			except ObjectDoesNotExist:
				try:
					Draft4Validator.check_schema(self.schema_json)
				except Exception as e:
					raise e
				else: 
					super(BadgeSchemaValidator, self).save(*args, **kwargs)

		# Save the model if it's an update.
		else:
			super(BadgeSchemaValidator, self).save(*args, **kwargs)

	# TODO: implement like the save override in OpenBadge
	# def __init__(self, scheme, validator_json, *args,**kwargs):
	# 	self.scheme = scheme
		
		


class OpenBadge(basic_models.SlugModel):
	"""
	Each OpenBadge contains an input Badge Object and corresponding metadata built up as a result of analysis.

	self.badge_input: string -- The badgeObject input to the library to analyze
	self.full_badge_object: (JSONField) dict of dicts -- of badgeObjects composed to add up to this badgeObject
	self.verify_method: string -- 'hosted' or 'signed'
	self.errors: list -- a list of critical OpenBadgeErrors 
	self.notes: list -- a list of validation passes and noncritical failures
	"""
	image = models.ImageField(upload_to='uploads/badges/received', blank=True)
	badge_input = models.TextField(blank=True, null=True)
	recipient_input = models.CharField(blank=True, max_length=2048)
	full_badge_object = JSONField()
	verify_method = models.CharField(max_length=48, blank=True)
	errors = JSONField()
	notes = JSONField()

	scheme = models.ForeignKey(BadgeScheme, blank=True, null=True)

	search = SphinxSearch()


	# Core procedure for filling out an OpenBadge from an initial badgeObject follows:
	def save(self, *args, **kwargs):
		if not self.pk:

			"""
			Stores the input object and sets up a fullBadgeObject to fill out and analyze
			"""
			if not self.image and self.recipient_input:
				raise IOError("Invalid input to OpenBadge create: " + kwargs['image'])

			self.errors = []
			self.notes = []

			try:
				self.badge_input = badgeanalysis.utils.extract_assertion_from_image(self.image)
			except Exception as e:
				self.errors.append(e)
				raise e
				return

			self.verify_method = 'hosted' #signed not yet supported.
			

			# Process the initial input
			# Returns a dict with badgeObject property for processed object and 'type', 'context', 'id' properties
			try:
				structureMeta = self.processBadgeObject(self.badge_input,'assertion')
			except TypeError as e:
				self.errors.append(e)
				raise e
				return

			if not structureMeta['badgeObject']:
				raise IOError("Could not build a full badge object without having a properly stored inputObject")

			full = {
				'@context': structureMeta['context'] or 'http://standard.openbadges.org/1.1/context',
				'@type': 'obi:OpenBadge'
			}
			# place the validated input object into 
			full[structureMeta['type']] = structureMeta['badgeObject'].copy()
		
			
			"""
			# Build out the full badge object by fetching missing components.
			
			#TODO: refactor. This is kind of clunky. Maybe some recursion would help
			#TODO: refactor to consider the future possibility of issuer defined in the assertion 
			#(or separate issuers defined in assertion & issuer, both cases requiring authorization)
			"""
			try:
				if isinstance(full['assertion'], dict) and not 'badgeclass' in full:
					# For 1.0 etc compliant badges with linked badgeclass
					if isinstance(full['assertion']['badge'], str):
						full['badgeclass'] = self.processBadgeObject(badgeanalysis.utils.fetch_linked_component(full['assertion']['badge']), 'badgeclass')
					# for nested badges (0.5 & backpack-wonky!)
					elif isinstance(full['assertion']['badge'], dict):
						full['badgeclass'] = full['assertion']['badge']

				if isinstance(full['badgeclass'], dict) and not 'issuerorg' in full:
					if isinstance(full['badgeclass']['issuer'], str):
						full['issuerorg'] = self.processBadgeObject(badgeanalysis.utils.fetch_linked_component(full['badgeclass']['issuer']), 'issuerorg')
					elif isinstance(full['badgeclass']['issuer'], dict):
						full['issuerorg'] = full['badgeclass']['issuer']
			except Exception as e:
				#TODO Add errors to openBadge instead
				self.errors.append(e)

			# Store results
			self.full_badge_object = full

		#finally, save the OpenBadge after doing all that stuff in case it's a new one
		super(OpenBadge, self).save(*args, **kwargs)


	def processBadgeObject(self, badgeObject, probableType='assertion'):
		structureMeta = {}

		if isinstance(badgeObject, (str, unicode)) and badgeanalysis.utils.test_probable_url(badgeObject):
			structureMeta['id'] = badgeObject
			try: 
				badgeObject = badgeanalysis.utils.test_probable_url(badgeObject)
			except Exception as e:
				raise TypeError("Couldn't fetch badgeObject on input. We tried to load " + badgeObject + " -- got error " + e)
				return

		if not isinstance(badgeObject, dict):
			badgeObject = badgeanalysis.utils.try_json_load(badgeObject)

		structureMeta['badgeObject'] = badgeObject

		""" CASE 1: For OBI version 1.1 and later, the badgeObject will have JSON-LD context information. """
		if badgeanalysis.utils.has_context(badgeObject):
			context = badgeObject.get('@context')

			# Determine if the existing context has a suitable main OBI context within it. 
			if isinstance(context, (str, list)):
				structureMeta['context'] = self.validateMainContext(context)

			# Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
			elif isinstance(context, dict):
				raise TypeError("OBI context not linked at top level of input object. This isn't a declared OBI object. Here's the context: " + context)


			if '@type' in badgeObject:
				#TODO this is likely not going to be the full expanded IRI, likely a fragment
				structureMeta['type'] = self.validateObiType(badgeObject['@type'])
			else:
				#TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
				# For now, assume we can guess the type correctly
				structureMeta['type'] = probableType
				structureMeta['badgeObject']['@type'] = probableType

			# """ CASE 2: For OBI versions 0.5 and 1.0, we will have to deterimine how to add JSON-LD context information. """
		else:

			#TODO: In progress, Use the BadgeScheme class to divine which of the old formats it might be.
			matchingScheme = BadgeScheme.test_against_schema_tree(badgeObject, probableType)
			if matchingScheme == None:
				raise TypeError("Could not determine type of badge object with known schema set")
				return None

			else:
				potentialContext = badgeSchemes.schema_context( matchingSchemaKey )
				structureMeta['context'] =  potentialContext
				structureMeta['badgeObject']['@context'] = potentialContext

				potentialType = badgeSchemes.schema_type( matchingScheme.context_url )
				structureMeta['type'] = potentialType
				structureMeta['badgeObject']['@type'] = potentialType

		""" Finalize badge object by adding the @id if possible """
		if 'id' in structureMeta and not '@id' in badgeObject:
			structureMeta['badgeObject']['@id'] = self.validateId(structureMeta['id'])
		elif '@id' in badgeObject:
			structureMeta['id'] = self.validateId(badgeObject['@id'])
		elif 'verify' in badgeObject and 'type' in badgeObject['verify'] and badgeObject['verify']['type'] == 'hosted' and 'url' in badgeObject['verify']:
			potentialId = self.validateId(badgeObject['verify']['url'])
			structureMeta['badgeObject']['@id'] = potentialId
			structureMeta['id'] = potentialId

		return structureMeta


	def validateMainContext(self, contextInput):
		url = re.compile(r"standard\.openbadges\.org/[\d\.]+/context$")
		if isinstance(contextInput, str) and url.search(contextInput):
			return contextInput
		elif isinstance(contextInput, list):
			for contextElement in context:
				if self.validateMainContext(contextElement):
					return contextElement
		elif isinstance(contextInput, dict):
			# no need to accept these for now
			pass
		return None

	# Gets a simple string (compact IRI in the OBI context of the OBI object type)
	def validateObiType(self, typeInput):
		#TODO rework this with JSON-LD compaction instead of a simple in set operation. Gotta handle full IRIs

		if isinstance(typeInput, str) and typeInput in ('assertion', 'badgeclass', 'issuerorg'):
			return typeInput

		elif isinstance(typeInput, list):
			for typeElement in typeInput:
				elType = self.validateObiType(typeElement)
				if elType != None:
					return elType
		return None
		

	def validateId(self, idString):
		if badgeanalysis.utils.test_probable_url(idString):
			return idString
		return None


	# Tools to inspect an initialized badge object
	def getProp(self, parent, prop):
		sourceObject = self.full_badge_object.get(parent)
		return sourceObject.get(prop)

	def getLdProp(self, parent, iri):
		sourceObject = self.full_badge_object.get(parent)
		options = { "documentLoader": self.custom_context_docloader }
		expanded = jsonld.expand(sourceObject, options)
		temp = expanded[0].get(iri)


		if len(temp) ==1:
			if '@value' in temp[0]:
				return temp[0]['@value']
			elif '@id' in temp[0]:
				return temp[0]['@id']
		else: 
			return temp 

	def custom_context_docloader(self, url):
		filename = BadgeScheme.get_context_file_by_url(url)
		if filename is not None:
			doc = {
				'contextUrl': None,
				'documentUrl': url,
				'document': load_context_from_filesystem(filename)
			}
			return doc

		#fall back to default document loader
		return jsonld.load_document(url)


class BadgeSchemes(object):
	def __init__(self):
		self.schemes = {}

		# Plain Url of hosted assertion baked into badge image (late 2011)
		self.schemes['plainurl'] = BaseBadgeScheme({
			'contextUrl': 'http://standard.openbadges.org/0.5/context',
			'contextFile': '0.5.json'
		})
		self.schemes['plainurl'].registerValidationSchema({
			'validatesType': 'assertion',
			'validationSchemaFile': 'plainuri.json',
			'validationSchema': 'http://standard.openbadges.org/0.5/schema/v0.5-plainuri',
		})
				
		# 0.5.0 Assertion baked into badge image (2012 - Spring 2013)
		self.schemes['v0_5'] = BaseBadgeScheme({
			'contextUrl': 'http://standard.openbadges.org/0.5/context',
			'contextFile': '0.5.json'	
		})
		self.schemes['v0_5'].registerValidationSchema({
			'validatesType': 'assertion',
			'validationSchemaFile': 'OBI-v0.5-assertion.json',
			'validationSchema': 'http://standard.openbadges.org/0.5/schema/v0.5-assertion',
		})

		# 1.0 Strict: Badge Class and Issuer objects linked in assertion (Spring 2013 - Fall 2014)
		self.schemes['v1_0strict'] = BaseBadgeScheme({
			'contextUrl': 'http://standard.openbadges.org/1.0/context',
			'contextFile': '1.0.json'	
		})
		self.schemes['v1_0strict'].registerValidationSchema({
			'validatesType': 'assertion',
			'validationSchemaFile': 'OBI-v1.0-linked-badgeclass.json',
			'validationSchema': 'http://standard.openbadges.org/1.0/schema/v1.0-assertion-linked-badgeclass',
		})

		# Backpack Mangled 1.0 badge (Fall 2013 - Fall 2014) that looks like an 0.5 badge
		self.schemes['backpack_error_1_0'] = BaseBadgeScheme({
				'contextUrl': 'http://standard.openbadges.org/0.5/context/',
				'contextFile': '0.5'
			})
		self.schemes['backpack_error_1_0'].registerValidationSchema({
			'validatesType': 'assertion',
			'validationSchema': 'http://standard.openbadges.org/0.5/schema/v0.5-1.0-mashed-up',
			'validationSchemaFile': 'backpack-error-from-valid-1.0.json'
		})

		# 1.1 JSON-LD enabled Open Badge Objects (Fall 2014 - )
		self.schemes['v1_1'] = BaseBadgeScheme()
		self.schemes['v1_0strict'].registerValidationSchema({
			'validatesType': 'assertion',
			'validationSchemaFile': 'OBI-v1.1-assertion',
			'validationSchema': 'http://standard.openbadges.org/1.1/schema/1.1-assertion',
		})

		self.SCHEME_TREE = {}
		self.SCHEME_TREE['assertion'] = {
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
		self.SCHEME_TREE['badgeclass'] = {}
		self.SCHEME_TREE['issuerorg'] = {}

	def tree_for(self, type):
		if type in ('assertion', 'badgeclass', 'issuerorg'):
			return SCHEME_TREE[type]
		return SCHEME_TREE['assertion']



	# Methods for getting Scheme metadata
	def schema_filename(self, schemeKey, type='assertion'):
		# returns first schema filename matched by type
		for validator in self.schemes[schemeKey]['validation']:
			if validator['validatesType'] == type:
				return validator['validationSchemaFile']
		return None
	
	def default_type(self, schemeKey):
		return self.schemes[schemeKey]['defaultType']

	

	def get_schemeKey_by_context_url(self, url):
		for key in self.schemes:
			if url == self.schemes[key]['contextUrl']:
				return key
		return None

	def schema_context(self, schemeKey):
		return self.schemes[schemeKey]['contextUrl']

	def schema_contextFile(self, schemeKey):
		return self.schemes[schemeKey]['contextFile']





