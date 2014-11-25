from django.db import models
import basic_models
from django.core.urlresolvers import reverse

import badgeanalysis.utils
from badgeanalysis.models import OpenBadge
# from badgeanalysis.utils import analyze_image_upload

class Certificate(basic_models.TimestampedModel):
	open_badge = models.ForeignKey(OpenBadge)

	def get_form(self):
		from certificates.forms import CertificateForm
		return CertificateForm(instance=self)

	def get_absolute_url(self):
		return reverse('certificate_detail', kwargs= {'pk': self.id} )

	def __unicode__(self):
		return "%s: %s" % (self.created_at, self.open_badge.__unicode__())
