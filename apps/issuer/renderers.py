from rest_framework.renderers import BrowsableAPIRenderer

import utils


class BadgeInstanceHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'issuer/badge_instance_detail.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(BadgeInstanceHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        context['badge_instance'] = renderer_context['badge_instance']
        context['badge_class'] = renderer_context['badge_class']
        context['issuer'] = renderer_context['issuer']

        recipient_email = renderer_context['badge_instance'].recipient_identifier
        context['obscured_recipient'] = utils.obscure_email_address(recipient_email)

        return context