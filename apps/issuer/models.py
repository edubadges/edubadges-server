from django.db import models
import basic_models
import django.template.loader

from badgeanalysis.models import OpenBadge
from badgeuser.models import BadgeUser

class Issuer(basic_models.SlugModel):
    url = models.URLField(verbose_name='Issuer\'s homepage', max_length=2048)
    issuer_object_url = models.URLField(max_length=2048, verbose_name='URL Location of the OBI Issuer file in JSON')
    description = models.TextField(blank=True)
    owner_user = models.ForeignKey(BadgeUser, related_name='owner', on_delete=models.PROTECT, null=False)

    def get_form(self):
        from issuer.forms import IssuerForm
        return IssuerForm(instance=self)


class EarnerNotification(basic_models.TimestampedModel):
    url = models.URLField(verbose_name='Assertion URL', max_length=2048)
    email = models.EmailField(max_length=254, blank=False)
    badge = models.ForeignKey(OpenBadge, blank=True, null=True)

    def get_form(self):
        from issuer.forms import NotifyEarnerForm
        return NotifyEarnerForm(instance=self)

    def send_email(self):
        ob = self.badge
        email_context = {
            'badge_name': ob.ldProp('bc', 'name'),
            'badge_description': ob.ldProp('bc', 'description'),
            'issuer_name': ob.ldProp('iss', 'name'),
            'issuer_url': ob.ldProp('iss', 'url'),
            'image_url': ob.get_baked_image_url()
        }
        t = django.template.loader.get_template('issuer/notify_earner_email.txt')
        ht = django.template.loader.get_template('issuer/notify_earner_email.html')
        text_output_message = t.render(email_context)
        html_output_message = ht.render(email_context)
        mail_meta = {
            'subject': 'Congratulations, you earned a badge!',
            'from_address': email_context['issuer_name'] + ' Badges <noreply@oregonbadgealliance.org>',
            'to_addresses': [self.email]
        }

        try:
            from django.core.mail import send_mail
            send_mail(
                mail_meta['subject'],
                text_output_message,
                mail_meta['from_address'],
                mail_meta['to_addresses'],
                fail_silently=False,
                html_message=html_output_message
            )
        except Exception as e:
            raise e
