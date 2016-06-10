from django.core.urlresolvers import reverse
from rest_framework.renderers import BrowsableAPIRenderer

import utils
from mainsite.utils import OriginSetting


class BadgeInstanceHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'issuer/badge_instance_detail.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeInstanceHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        try:
            context['badge_instance'] = renderer_context['badge_instance']
            context['badge_class'] = renderer_context['badge_class']
            context['issuer'] = renderer_context['issuer']
            context['badge_instance_image_url'] = OriginSetting.HTTP+renderer_context['badge_instance'].image.url
            context['badge_instance_public_url'] = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={
                'slug': renderer_context['instance'].slug})

            recipient_email = renderer_context['badge_instance'].recipient_identifier
            context['obscured_recipient'] = utils.obscure_email_address(recipient_email)
        except KeyError:
            pass

        return context


class BadgeClassCriteriaHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'issuer/badge_class_criteria.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeClassCriteriaHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        try:
            context['badge_class'] = renderer_context['badge_class']
            context['issuer'] = renderer_context['issuer']
        except KeyError:
            pass

        return context
