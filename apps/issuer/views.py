import json

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView

from badgeuser.serializers import UserProfileField
from mainsite import settings

from .serializers import IssuerPortalSerializer


class IssuerPortal(TemplateView):
    template_name = 'base.html'

    def get(self, request):
        if not request.user.is_authenticated():
            return redirect(reverse('login'))

        context = self.get_context_data(**{'request': request})
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super(IssuerPortal, self).get_context_data(**kwargs)
        issuer_serializer = IssuerPortalSerializer(kwargs['request'].user, context=kwargs)

        context = {}
        context['issuer_issuers'] = issuer_serializer.data['issuer_issuers']
        context['issuer_badgeclasses'] = issuer_serializer.data['issuer_badgeclasses']
        context['user'] = UserProfileField(kwargs['request'].user, context=kwargs).data
        context['installed_apps'] = issuer_serializer.data['installed_apps']
        context['STATIC_URL'] = settings.STATIC_URL

        context_data['initial_data'] = json.dumps(context)
        return context_data
