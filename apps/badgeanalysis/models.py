import re
import utils

class InfoObject:
	"""
	Each InfoObject contains an input Badge Object and corresponding metadata built up as a result of analysis.

	self.inputObject
	self.id: str -- the IRI of the badgeObject
	self.inputVersionContext: str -- an IRI with our best guess of the context to use for this badge 
	self.inputObjectType: str -- an IRI corresponding to the version and type of this badge object. e.g. a v1.1 Assertion
	self.fullBadgeObject: dict of dicts -- of badgeObjects composed to add up to this badgeObject
	self.verifyMethod: string -- 'hosted' or 'signed'
	"""

	def __init__(self, badgeObject):
		self.inputObject = badgeObject
	
	def setContext(contextString):	
		if isinstance(contextString, str) and re.match(r"standard\.openbadges\.org/[\d\.]+/context$",contextString):
			self.inputVersionContext = contextString

	def setType(typeString):
		if re.match(r"^http", typeString):
			self.inputObjectType = typeString
		elif re.search(r"assertion", typeString, flags=re.I):
			self.inputObjectType = 'http://standard.openbadges.org/definitions#Assertion'

	def setId(idString): 
		self.id = idString

	def initFullBadgeObject():
		context = self.inputVersionContext or 'http://standard.openbadges.org/1.1/context'

		full = {
			'@context': context
		}

