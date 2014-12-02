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
        context['badge_name'] = badge.ldProp('bc', 'name')
        context['badge_description'] = badge.ldProp('bc', 'description')
        context['badge_image'] = badge.ldProp('bc', 'image')
        context['issue_date'] = badge.ldProp('asn', 'issuedOn')
        context['badge_issuer'] = badge.ldProp('iss', 'name')
        context['issuer_url'] = badge.ldProp('iss', 'url')

        context['recipient'] = badge.recipient_input

        context['baked_image_url'] = badge.ldProp('asn', 'image')
        if context['baked_image_url']:
            context['qrcode'] = "http://chart.googleapis.com/chart?cht=qr&chs=400x400&chl=" + context['baked_image_url']
        return context
