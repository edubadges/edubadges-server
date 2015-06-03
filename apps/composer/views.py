import json

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from badgeuser.serializers import UserProfileField

from .serializers import EarnerPortalSerializer


class EarnerPortal(TemplateView):
    template_name = 'base.html'

    def get(self, request):
        if not request.user.is_authenticated():
            return redirect(reverse('login'))

        context = self.get_context_data(**{'request': request})
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super(EarnerPortal, self).get_context_data(**kwargs)
        earner_serializer = EarnerPortalSerializer(kwargs['request'].user, context=kwargs)

        context = {}
        context['earner_collections'] = earner_serializer.data['earner_collections']
        context['earner_badges'] = earner_serializer.data['earner_badges']
        context['user'] = UserProfileField(kwargs['request'].user, context=kwargs).data
        context['installed_apps'] = earner_serializer.data['installed_apps']

        context_data['initial_data'] = json.dumps(context)
        return context_data
