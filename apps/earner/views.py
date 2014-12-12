from django.views.generic import CreateView, DetailView
from badgeuser.models import BadgeUser
from django.http import Http404

from mainsite.views import ActiveTabMixin
from earner.models import *  # EarnerBadge
from earner.forms import *  # EarnerBadgeCreateForm


class EarnerBadgeCreate(ActiveTabMixin, CreateView):
    model = EarnerBadge
    active_tab = 'earn'
    form_class = EarnerBadgeCreateForm


class EarnerPortal(ActiveTabMixin, DetailView):
    model = BadgeUser
    active_tab = 'earn'
    template_name = 'earner/earner_home.html'

    def get_object(self):
        current_user = self.request.user
        if current_user is not None:
            return current_user
        raise Http404

    def get(self, request):
        try:
            self.object = self.get_object()
        except Http404:
            # TODO: use reverse()
            return redirect('/login')
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)