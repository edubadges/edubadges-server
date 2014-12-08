from django.db import models
import basic_models

from badgeanalysis.models import OpenBadge


class Issuer(basic_models.SlugModel):
    url = models.URLField(verbose_name='Issuer\'s homepage', max_length=2048)
    issuer_object_url = models.URLField(max_length=2048, verbose_name='URL Location of the OBI Issuer file in JSON')
    description = models.TextField(blank=True)

    def get_form(self):
        from issuer.forms import IssuerForm
        return IssuerForm(instance=self)


class EarnerNotification(basic_models.TimestampedModel):
    url = models.URLField(verbose_name='Assertion URL', max_length=2048)
    email = models.EmailField(max_length=254, blank=False)
    # badge = models.ForeignKey(OpenBadge, blank=True)

    def get_form(self):
        from issuer.forms import NotifyEarnerForm
        return NotifyEarnerForm(instance=self)
