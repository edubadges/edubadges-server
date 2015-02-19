from django.views.generic import CreateView, DetailView
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from issuer.models import *

from badgeuser.serializers import BadgeUserSerializer
import json


# from django.shortcuts import render_to_response


class IssuerCreate(CreateView):
    model = Issuer


class IssuerDetail(DetailView):
    model = Issuer


class EarnerNotificationCreate(CreateView):
    template_name = 'base_interior.html'
    model = EarnerNotification

    def get_current_user(self):
        current_user = self.request.user
        if current_user is not None:
            return current_user
        raise Http404

    def get(self, request):
        try:
            self.object = self.get_current_user()
        except Http404:
            return redirect(reverse('login'))
        context = self.get_context_data(user=self.object)

        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('notify_earner')

    def get_context_data(self, **kwargs):
        context = super(EarnerNotificationCreate, self).get_context_data(**kwargs)
        user_serializer = BadgeUserSerializer(kwargs['user'])

        context['initial_data'] = json.dumps(user_serializer.data)

        return context
