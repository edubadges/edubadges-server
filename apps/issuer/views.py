from django.views.generic import CreateView, DetailView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from issuer.models import *
from mainsite.views import ActiveTabMixin
from issuer.forms import IssuerForm, NotifyEarnerForm


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
    form_class = NotifyEarnerForm

    def form_invalid(self, form):
        return super(EarnerNotificationCreate, self).form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.badge = form.cleaned_data['badge']

        try:
            self.object.send_email(**{'request': self.request})
        except Exception:
            # TODO: make this work
            self.form_invalid(form)
        else:
            self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('notify_earner')

    def get_context_data(self, **kwargs):
        context = super(EarnerNotificationCreate, self).get_context_data(**kwargs)
        return context
