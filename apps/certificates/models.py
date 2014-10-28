from django.db import models
import basic_models
from django.core.urlresolvers import reverse


class Certificate(basic_models.TimestampedModel):
    image = models.ImageField(upload_to='certificates')

    # def save(self, *args, )
    def get_absolute_url(self):
        return reverse('certificate_detail', kwargs= {'pk': self.id} )

    def __unicode__(self):
        return "%s: %s" % (self.created_at, self.image.url)