from django.views.generic import *
from certificates.models import *
from django.core.urlresolvers import reverse_lazy

from mainsite.views import ActiveTabMixin
from badgeanalysis.forms import BadgeSchemeForm
from badgeanalysis.models import BadgeScheme

import json

class BadgeSchemeCreate(ActiveTabMixin, CreateView):
    model = BadgeScheme
    active_tab = 'badgeschemes'
    form_class = BadgeSchemeForm
    

class BadgeSchemeDetail(ActiveTabMixin, UpdateView):
    model = BadgeScheme
    active_tab = 'badgeschemes'
    form_class = BadgeSchemeForm

    def get_context_data(self, **kwargs):
    	context = super(BadgeSchemeDetail, self).get_context_data(**kwargs)
    	return context

class BadgeSchemeDelete(ActiveTabMixin, DeleteView):
	model = BadgeScheme
	active_tab = 'badgeschemes'
	success_url = reverse_lazy('badgescheme_create')