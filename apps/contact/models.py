from django.db import models
import basic_models


class Submission(basic_models.TimestampedModel):
    name = models.CharField(max_length=300)
    email = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=300, blank=True)
    message = models.TextField(blank=True)

    def __unicode__(self):
        return "%s (%s)" % (self.name, self.email)