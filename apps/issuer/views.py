from django.views.generic import CreateView, DetailView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from issuer.models import *
from mainsite.views import ActiveTabMixin
from issuer.forms import IssuerForm
from badgeanalysis.models import OpenBadge

import django.template.loader
# from django.shortcuts import render_to_response


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

        try:
            ob = OpenBadge(recipient_input=form.cleaned_data['email'], badge_input=form.cleaned_data['url'])
            ob.save()
        except Exception as e: 
            raise e

        email_context = {
            'badge_name': ob.ldProp('bc', 'name'),
            'badge_description': ob.ldProp('bc', 'description'),
            'issuer_name': ob.ldProp('iss', 'name'),
            'issuer_url': ob.ldProp('iss', 'url'),
            'image_url': form.cleaned_data['url'] + '/image'
        }
        t = django.template.loader.get_template('issuer/notify_earner_email.txt')
        ht = django.template.loader.get_template('issuer/notify_earner_email.html')
        text_output_message = t.render(email_context)
        html_output_message = ht.render(email_context)
        mail_meta = {
            'subject': 'Congratulations, you earned a badge!',
            'from_address': email_context['issuer_name'] + ' Badges <noreply@oregonbadgealliance.org>',
            'to_addresses': [form.cleaned_data['email']]
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
            self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('notify_earner')
