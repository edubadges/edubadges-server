from django.views.generic import CreateView, DetailView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from issuer.models import *
from mainsite.views import ActiveTabMixin
from issuer.forms import IssuerForm
from badgeanalysis.models import OpenBadge


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
        return super(EarnerNotificationCreate, self).form_invalid(form)

    def form_valid(self, form):
        import pdb; pdb.set_trace();

        try:
            badge = OpenBadge(recipient_input=form.cleaned_data['email'], badge_input=form.cleaned_data['url'])
            badge.save()
        except Exception:
            self.form_invalid()

        self.object = form.save(commit=False)
        self.object.badge = badge
        self.object.save()

        try:
            self.object.send_email()
        except Exception:
            self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('notify_earner')
