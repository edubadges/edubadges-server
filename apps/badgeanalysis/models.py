import re
from badgeanalysis.utils import has_context, test_against_schema_tree, schema_context, schema_type, custom_context_docloader, fetch_linked_component, tree_for

from pyld import jsonld


class OpenBadge(object):
	"""
	Each OpenBadge contains an input Badge Object and corresponding metadata built up as a result of analysis.

	self.inputObject: dict -- The badgeObject input to the library to analyze
	self.fullBadgeObject: dict of dicts -- of badgeObjects composed to add up to this badgeObject
	self.verifyMethod: string -- 'hosted' or 'signed'
	self.errors: list -- a list of critical OpenBadgeErrors 
	self.notes: list -- a list of validation passes and noncritical failures
	"""


	def __init__(self, badgeObject):
		"""
		Stores the input object and sets up a fullBadgeObject to fill out and analyze
		"""
		self.inputObject = badgeObject
		structureMeta = {}

		# For Badges with @context (post 1.0 badges)
		if has_context(badgeObject):
			context = badgeObject.get('@context')

			# Determine if the existing context has a suitable main OBI context within it. 
			if isinstance(context, (str, list)):
				structureMeta['context'] = self.validateMainContext(context)

			# Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
			elif isinstance(context, dict):
				raise JsonLdError("OBI context not linked at top level of input object")


			if '@type' in badgeObject:
				#TODO this is likely not going to be the full expanded IRI, likely a fragment
				structureMeta['type'] = self.validateObiType(badgeObject['@type'])
			else:
				#TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
				# For now, assume it's an assertion
				structureMeta['type'] = 'assertion'

			
		else:
			matchingSchemaKey = test_against_schema_tree(badgeObject)
			if matchingSchemaKey == None:
				raise TypeError("Could not determine type of badge object with known schema set")
				return

			# TODO: Implement case for 'plainurl' to fetch assertion then start_analysis(fetched_assertion)
			else:
				structureMeta['context'] = schema_context( matchingSchemaKey ) 
				structureMeta['type'] = schema_type( matchingSchemaKey )
			
		# for both cases, make sure we have the id	
		structureMeta['id'] = self.extract_ID_from_inputObject()

		self.initFullBadgeObject(**structureMeta)

	def processBadgeObject(self, badgeObject, probableType):
		structureMeta = {}
		if has_context(badgeObject):
			context = badgeObject.get('@context')

			# Determine if the existing context has a suitable main OBI context within it. 
			if isinstance(context, (str, list)):
				structureMeta['context'] = self.validateMainContext(context)

			# Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
			elif isinstance(context, dict):
				raise JsonLdError("OBI context not linked at top level of input object")


			if '@type' in badgeObject:
				#TODO this is likely not going to be the full expanded IRI, likely a fragment
				structureMeta['type'] = self.validateObiType(badgeObject['@type'])
			else:
				#TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
				# For now, assume it's an assertion
				structureMeta['type'] = probableType

		else:
			matchingSchemaKey = test_against_schema_tree(badgeObject, testTree=tree_for(probableType))
			if matchingSchemaKey == None:
				raise TypeError("Could not determine type of badge object with known schema set")
				return

			# TODO: Implement case for 'plainurl' to fetch assertion then start_analysis(fetched_assertion)
			else:
				structureMeta['context'] = schema_context( matchingSchemaKey ) 
				structureMeta['type'] = schema_type( matchingSchemaKey )

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

	def validateObiType(self, typeInput):
		#TODO rework this with JSON-LD compaction instead of a simple regex
		if isinstance(typeInput, str) and re.search(r"assertion", typeInput, flags=re.I):
			return 'assertion'
		elif isinstance(typeInput, list):
			for typeElement in typeInput:
				elType = self.validateObiType(typeElement)
				if elType != None:
					return elType
		return None

	def extract_ID_from_inputObject(self):
		badgeObject = self.inputObject
		if '@id' in badgeObject:
			return self.validateId(badgeObject['@id'])
		elif 'verify' in badgeObject and 'type' in badgeObject['verify'] and badgeObject['verify']['type'] == 'hosted' and 'url' in badgeObject['verify']:
			return self.validateId(badgeObject['verify']['url'])


	def validateId(self, idString):
		#TODO, make sure it's an IRI 
		return idString

	def initFullBadgeObject(self, **kwargs):
		# Make sure we're ready to build a full object
		#raise IOError(kwargs)
		context = kwargs['context'] or 'http://standard.openbadges.org/1.1/context'
		inputType = kwargs['type'] or 'assertion'

		if not self.inputObject:
			raise IOError("Could not build a full badge object without having a properly stored inputObject")

		full = {
			'@context': context,
			'@type': 'obi:OpenBadge'
		}
		full[inputType] = self.inputObject.copy()
	
		firstObj = full[inputType]
		if not '@id' in firstObj and 'id' in kwargs:
			firstObj['@id'] = kwargs['id']
		if not '@type' in firstObj:
			firstObj['@type'] = inputType

		self.fullBadgeObject = full

		

	def fill_missing_components(self):
		fullObject = openBadge.fullBadgeObject
		#TODO: refactor. This is kind of clunky. Maybe some recursion would help
		try:
			if isinstance(fullObject['assertion'], dict) and not 'badgeclass' in fullObject:
				# For 1.0 etc compliant badges with linked badgeclass
				if isinstance(fullObject['assertion']['badge'], str):
					fullObject['badgeclass'] = fetch_linked_component(fullObject['assertion']['badge'])
				# for nested badges (0.5 & backpack-wonky!)
				elif isinstance(fullObject['assertion']['badge'], dict):
					fullObject['badgeclass'] = fullObject['assertion']['badge']

			if isinstance(fullObject['badgeclass'], dict) and not 'issuerorg' in fullObject:
				if isinstance(fullObject['badgeclass']['issuer'], str):
					fullObject['issuerorg'] = fetch_linked_component(fullObject['badgeclass']['issuer'])
				elif isinstance(fullObject['badgeclass']['issuer'], dict):
					fullObject['issuerorg'] = fullObject['badgeclass']['issuer']
		except Exception as e:
			#TODO Add errors to openBadge instead
			raise e
		validate_object(openBadge)

	def validate_object(self):
		# TODO
		pass


	# Tools to inspect an initialized badge object
	def getProp(self, parent, prop):
		sourceObject = self.fullBadgeObject.get(parent)
		return sourceObject.get(prop)

	def getLdProp(self, parent, iri):
		sourceObject = self.fullBadgeObject.get(parent)
		options = { "documentLoader": custom_context_docloader }
		expanded = jsonld.expand(sourceObject, options)
		temp = expanded[0].get(iri)


		if len(temp) ==1:
			if '@value' in temp[0]:
				return temp[0]['@value']
			elif '@id' in temp[0]:
				return temp[0]['@id']
		else: 
			return temp 



