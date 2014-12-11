from django.views.generic import CreateView, DetailView
from django.contrib.auth.models import User

from mainsite.views import ActiveTabMixin
from earner.models import *  # EarnerBadge
from earner.forms import *  # EarnerBadgeCreateForm


class EarnerBadgeCreate(ActiveTabMixin, CreateView):
    model = EarnerBadge
    active_tab = 'earn'
    form_class = EarnerBadgeCreateForm


class EarnerPortal(ActiveTabMixin, DetailView):
    model = User
    active_tab = 'earn'
    template_name = 'earner/earner_home.html'

    def get_object(self):
        return self.request.user
