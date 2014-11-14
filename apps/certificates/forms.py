from django import forms
from django.forms.widgets import HiddenInput
import json
from badgeanalysis.utils import extract_assertion_from_image

from certificates.models import Certificate
from badgeanalysis.models import OpenBadge

class CertificateForm(forms.ModelForm):
	image = forms.ImageField()
	recipient = forms.EmailField()

	class Meta:
		model = Certificate
		fields = ()

	# def clean(self):
	# 	self.cleaned_data = super(CertificateForm, self).clean()

	# 	image_upload = self.cleaned_data.get('image')
	# 	recipient = self.cleaned_data.get('recipient')

	# 	return self.cleaned_data

	def save(self, *args, **kwargs):
		#On save, create an Open Badge Item for the image uploaded for this certificate

	# try:
		badge = OpenBadge(image=self.cleaned_data['image'], recipient_input=self.cleaned_data['recipient'])
		badge.save()
	# except Exception as e:
	# 	raise e
	# else:
		self.open_badge = badge

		super(CertificateForm, self).save()

