from django.views.generic import CreateView, DetailView
from badgeuser.models import BadgeUser
from django.http import Http404
import json

from mainsite.views import ActiveTabMixin
from earner.models import EarnerBadge
from earner.forms import EarnerBadgeCreateForm
from earner.serializers import EarnerBadgeSerializer


class EarnerBadgeCreate(ActiveTabMixin, CreateView):
    model = EarnerBadge
    active_tab = 'earn'
    form_class = EarnerBadgeCreateForm


class EarnerPortal(ActiveTabMixin, DetailView):
    model = BadgeUser
    active_tab = 'earn'
    template_name = 'base_interior.html'

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
        context = self.get_context_data(user=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):

        context_data = super(EarnerPortal, self).get_context_data(**kwargs)

        # Add the earner's badges to the context
        earner_badges_raw = EarnerBadge.objects.filter(earner=kwargs['user'])
        serializer = EarnerBadgeSerializer(earner_badges_raw, many=True)
        context_data['initial_data'] = {
            "earnerBadges": json.dumps(serializer.data)
        }
        
        return context_data