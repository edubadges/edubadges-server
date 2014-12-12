from django.db import models
import basic_models

from badgeanalysis.models import OpenBadge


class EarnerBadge(basic_models.SlugModel):
    badge = models.ForeignKey(OpenBadge, null=False)
    earner_description = models.TextField(blank=True)

    def get_form(self):
        from issuer.forms import IssuerForm
        return IssuerForm(instance=self)
