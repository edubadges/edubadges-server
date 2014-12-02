from django.views.generic import *
from certificates.models import *
from mainsite.views import ActiveTabMixin
from certificates.forms import CertificateForm


class CertificateCreate(ActiveTabMixin, CreateView):
    model = Certificate
    active_tab = 'certificates'
    form_class = CertificateForm


class CertificateDetail(ActiveTabMixin, DetailView):
    model = Certificate
    active_tab = 'certificates'

    def get_context_data(self, **kwargs):
        context = super(CertificateDetail, self).get_context_data(**kwargs)

        certificate = context['object']
        badge = certificate.open_badge
        context['badge_name'] = badge.getLdProp('http://standard.openbadges.org/definitions#BadgeClass', 'http://schema.org/name')
        context['badge_description'] = badge.getProp('badgeclass', 'description')
        context['badge_image'] = badge.getProp('badgeclass', 'image')
        context['issue_date'] = badge.getProp('assertion', 'issuedOn')
        context['badge_issuer'] = badge.getProp('issuerorg', 'name')
        context['issuer_url'] = badge.getProp('issuerorg', 'url')

        context['recipient'] = badge.recipient_input

        context['baked_image_url'] = badge.getProp('assertion', 'image')
        if context['baked_image_url']:
            context['qrcode'] = "http://chart.googleapis.com/chart?cht=qr&chs=400x400&chl=" + context['baked_image_url']
        return context
