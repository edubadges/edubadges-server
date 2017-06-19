import urllib

from django.core.urlresolvers import reverse
from rest_framework.renderers import BrowsableAPIRenderer

import utils
from issuer.models import BadgeInstance
from mainsite.utils import OriginSetting


class BadgeInstanceHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'public/assertion.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeInstanceHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        badge_instance = renderer_context.get('badge_instance')

        obi_version = renderer_context.get('obi_version', utils.CURRENT_OBI_VERSION)
        context['obi_version'] = obi_version

        if badge_instance.source_url:
            context['external_source_url'] = badge_instance.source_url

        public_url = badge_instance.jsonld_id + '.json'

        if obi_version == utils.CURRENT_OBI_VERSION:
            context['badge_instance_public_url'] = public_url
        else:
            context['badge_instance_public_url'] = '{}?{}'.format(public_url, urllib.urlencode({'v': obi_version}))

        context['badgeclass_image_png'] = "{}{}?type=png".format(
            OriginSetting.HTTP,
            reverse('badgeclass_image', kwargs={'entity_id': renderer_context['badge_class'].entity_id})
        )

        context.update(renderer_context)
        context['issuer_url'] = context['issuer'].jsonld_id
        context['badge_instance_image_url'] = badge_instance.image.url if renderer_context['badge_instance'].image else None

        recipient_email = badge_instance.recipient_identifier
        context['obscured_recipient'] = utils.obscure_email_address(recipient_email)

        if obi_version == '1_1':
            context['alt_url'] = '{}?{}'.format(context['request'].path, urllib.urlencode({'v': '2_0'}))
            context['alt_version_name'] = '2.0'
        elif obi_version == '2_0':
            context['alt_url'] = context['request'].path
            context['alt_version_name'] = '1.1'

        return context


class BadgeClassHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'public/badge_class.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeClassHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        try:
            context['badge_class'] = renderer_context['badge_class']
            context['issuer'] = renderer_context['issuer']
            context['badgeclass_count'] = renderer_context['badgeclass_count']
            if renderer_context['badge_class'].source_url:
                context['external_source_url'] = renderer_context['badge_class'].source_url
        except KeyError:
            pass

        return context


class IssuerHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'public/issuer.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(IssuerHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        try:
            context['issuer'] = renderer_context['issuer']
            context['badge_classes'] = renderer_context['badge_classes']
            if renderer_context['issuer'].source_url:
                context['external_source_url'] = renderer_context['issuer'].source_url
        except KeyError:
            pass

        return context
