from django.views.generic import CreateView, DetailView
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from issuer.models import *
from mainsite.views import ActiveTabMixin
from issuer.forms import IssuerForm

from django.db.models.query import EmptyQuerySet
# from django.core.exceptions import DoesNotExist
import django.template.loader
from django.shortcuts import render_to_response


class IssuerCreate(ActiveTabMixin, CreateView):
    model = Issuer
    active_tab = 'issuer'
    form_class = IssuerForm


class IssuerDetail(ActiveTabMixin, DetailView):
    model = Issuer
    active_tab = 'issuer'
    form_class = IssuerForm


class EarnerNotificationCreate(ActiveTabMixin, CreateView):
    active_tab = 'issuer'
    template_name = 'issuer/notify_earner.html'
    model = EarnerNotification

    def form_invalid(self, form):
        return super(EarnerNotification, self).form_invalid(form)

    def form_valid(self, form):

        email_context = {
            'badge_name': 'TEST BADGE #1',
            'badge_description': "A description of the test badge. This description is most accurate and complete!",
            'issuer_name': "Distinctive Badges, Inc.",
            'issuer_url': 'http://silly-willy.com',
            'image_url': "http://placekitten.com/300/300"
        }
        t = django.template.loader.get_template('issuer/notify_earner_email.txt')
        ht = django.template.loader.get_template('issuer/notify_earner_email.html')
        text_output_message = t.render(email_context)
        html_output_message = ht.render(email_context)
        mail_meta = {
            'subject': 'Congratulations, you earned a badge!',
            'from_address': 'OregonASK Badges <noreply@Doregonbadgealliance.org>',
            'to_addresses': ['ottonomy+test@gmail.com']
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
            response_context = {"error": str(e)}
            import pdb; pdb.set_trace();
            self.form_invalid(form)

        return HttpResponse.HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('notify_earner')
