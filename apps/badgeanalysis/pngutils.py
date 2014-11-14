import png
import re
import hashlib

def extract(imageFile):
	"""
	Return the openbadges content contained in a baked PNG file. 
	If this doesn't work, return None.

	If there is both an iTXt and tEXt chunk with keyword openbadges, 
	the iTXt chunk content will be returned.
	"""

	#if isinstance(src, basestring):
		# src = open(src, 'rb')

	reader = png.Reader(file=imageFile)
	for chunktype, content in reader.chunks():
		if chunktype == 'iTXt' and content.startswith('openbadges\x00'):
			return re.sub('openbadges[\x00]+', '', content)
		elif chunktype == 'tEXt' and content.startswith('openbadges\x00'):  
			return content.split('\x00')[1]
