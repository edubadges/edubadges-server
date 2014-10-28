from django.db import models
from django.db.models import permalink
from django.conf import settings
from ckeditor.fields import HTMLField
from sky_thumbnails.fields import EnhancedImageField
import basic_models


class HomePage(basic_models.TimestampedModel, basic_models.OnlyOneActiveModel):
    body = HTMLField()

    def __unicode__(self):
        return str(self.created_at)

    @permalink
    def get_absolute_url(self):
        return ('home', None)