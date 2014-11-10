from django.db import models
import basic_models
from django.core.urlresolvers import reverse
from badgeanalysis.utils import analyze_image_upload

class Certificate(basic_models.TimestampedModel):
	image = models.ImageField(upload_to='certificates')
	analysis = models.TextField

	# def save(self, *args, )
	def get_absolute_url(self):
		return reverse('certificate_detail', kwargs= {'pk': self.id} )

	def __unicode__(self):
		return "%s: %s" % (self.created_at, self.image.url)

	def pre_save(self, model_instance, add):
		"Returns field's value just before saving."
		file = super(ImageField, self).pre_save(model_instance, add)
		model_instance.analysis = analyze_image_upload(file)
		return file

	# def save(self, *args, **kwargs):
		# On save, run analysis and save it to analysis
		
	# def clean(self):
 #        # Run analysis on image
 #        if self.image and self.analysis is None:
 #            raise ValidationError('Draft entries may not have a publication date.')
 #        # Set the pub_date for published items if it hasn't been set already.
 #        if self.status == 'published' and self.pub_date is None:
 #            self.pub_date = datetime.date.today()