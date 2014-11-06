import re
from badgeanalysis.utils import has_context, test_against_schema_tree, schema_context, schema_type
from pyld import jsonld


class OpenBadge(object):
	"""
	Each OpenBadge contains an input Badge Object and corresponding metadata built up as a result of analysis.

	self.inputObject: dict -- The badgeObject input to the library to analyze
	self.fullBadgeObject: dict of dicts -- of badgeObjects composed to add up to this badgeObject
	self.verifyMethod: string -- 'hosted' or 'signed'
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

			if '@id' in badgeObject:
				structureMeta['id'] = self.validateId(badgeObject['@id'])
			elif 'verify' in badgeObject and 'type' in badgeObject['verify'] and badgeObject['verity']['type'] == 'hosted' and 'url' in badgeObject['verify']:
				structureMeta['id'] = self.validateId(badgeObject['verify']['url'])

		else:
			matchingSchemaKey = test_against_schema_tree(badgeObject)
			if matchingSchemaKey == None:
				raise TypeError("Could not determine type of badge object with known schema set")
				return

			# TODO: Implement case for 'plainurl' to fetch assertion then start_analysis(fetched_assertion)
			else:
				structureMeta['context'] = schema_context( matchingSchemaKey ) 
				structureMeta['type'] = schema_type( matchingSchemaKey )
				

		self.initFullBadgeObject(**structureMeta)


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
			'@context': context
		}
		full[inputType] = self.inputObject.copy()
	
		firstObj = full[inputType]
		if not '@id' in firstObj and kwargs['id']:
			firstObj['@id'] = kwargs['id']
		if not '@type' in firstObj:
			firstObj['@type'] = inputType

		self.fullBadgeObject = full

	def getProp(self, parent, prop):
		sourceObject = self.fullBadgeObject.get(parent)
		return sourceObject.get(prop)


