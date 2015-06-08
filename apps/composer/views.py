import json

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic import DetailView, TemplateView

from badgeuser.serializers import UserProfileField

from .models import Collection
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


class CollectionDetailView(DetailView):
    model = Collection
    context_object_name = 'collection'

    def get(self, request, *args, **kwargs):
        response = super(CollectionDetailView, self).get(request, *args, **kwargs)
        print self.object.share_hash
        print kwargs.get('share_hash')
        if self.object.share_hash != kwargs.get('share_hash'):
            return HttpResponse('Unauthorized', status=401)
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(CollectionDetailView, self).get_context_data(*args, **kwargs)

        context.update({
        })
        return context
