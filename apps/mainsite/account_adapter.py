from django.conf import settings

from allauth.account.adapter import DefaultAccountAdapter


class BadgrAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        context['STATIC_URL'] = getattr(settings, 'STATIC_URL')
        context['HTTP_ORIGIN'] = getattr(settings, 'HTTP_ORIGIN')

        msg = self.render_mail(template_prefix, email, context)
        msg.send()
