from django.views.generic import DetailView
from django.contrib.auth.models import AnonymousUser
from badgeuser.models import BadgeUser
from django.http import Http404
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from badgeuser.serializers import BadgeUserSerializer
import json


class EarnerPortal(DetailView):
    model = BadgeUser
    template_name = 'base_interior.html'

    def get_object(self):
        current_user = self.request.user
        if current_user is not None and current_user.is_authenticated():
            return current_user
        raise Http404

    def get(self, request):
        try:
            self.object = self.get_object()
        except Http404:
            # TODO: use reverse()
            return redirect(reverse('login'))
        context = self.get_context_data(user=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super(EarnerPortal, self).get_context_data(**kwargs)
        user_serializer = BadgeUserSerializer(kwargs['user'])

        context_data['initial_data'] = json.dumps(user_serializer.data)

        return context_data
