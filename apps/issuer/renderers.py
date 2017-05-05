from django.core.urlresolvers import reverse
from rest_framework.renderers import BrowsableAPIRenderer

import utils
from mainsite.utils import OriginSetting


class BadgeInstanceHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'public/assertion.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeInstanceHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        try:
            context['badgeclass_image_png'] = "{}{}?type=png".format(
                OriginSetting.HTTP,
                reverse('badgeclass_image', kwargs={'entity_id': renderer_context['badge_class'].entity_id})
            )

            context.update(renderer_context)
            context['issuer_url'] = context['issuer'].jsonld_id
            context['badge_instance_image_url'] = renderer_context['badge_instance'].image.url if renderer_context['badge_instance'].image else None
            context['badge_instance_public_url'] = renderer_context['badge_instance'].jsonld_id
            context['badgeclass_count'] = renderer_context['badgeclass_count']

            recipient_email = renderer_context['badge_instance'].recipient_identifier
            context['obscured_recipient'] = utils.obscure_email_address(recipient_email)
        except KeyError as e:
            pass

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
        except KeyError:
            pass

        return context
