import json
from django.conf import settings

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView, TemplateView

from badgeuser.serializers import UserProfileField
from issuer.models import BadgeInstance
from mainsite.utils import installed_apps_list

from .models import Collection, LocalBadgeInstance
from .serializers import CollectionSerializer, LocalBadgeInstanceUploadSerializer


class EarnerPortal(TemplateView):
    template_name = 'base.html'

    def get_context_data(self, **kwargs):
        """
        Pass initial data to a view template so that the React.js front end can
        render.
        """
        context = super(EarnerPortal, self).get_context_data(**kwargs)

        user_collections = CollectionSerializer(
            Collection.objects.filter(owner=self.request.user),
            many=True).data

        imported_badges = LocalBadgeInstance.objects.filter(recipient_user=self.request.user)
        local_badges = BadgeInstance.objects.filter(recipient_identifier__in=self.request.user.all_recipient_identifiers)
        all_badges = list(imported_badges) + list(local_badges)

        user_badges = LocalBadgeInstanceUploadSerializer(all_badges, many=True).data

        context.update({
            'initial_data': json.dumps({
                'earner_collections': user_collections,
                'earner_badges': user_badges,
                'installed_apps': installed_apps_list(),
                'user': UserProfileField(self.request.user, context=kwargs).data,
                'STATIC_URL': settings.STATIC_URL
            }),
        })

        return context


class CollectionDetailView(DetailView):
    model = Collection
    context_object_name = 'collection'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        response = super(CollectionDetailView, self).get(request, *args, **kwargs)

        if self.object.share_hash == '' or \
                self.object.share_hash != kwargs.get('share_hash'):
            return HttpResponse(
                'Unauthorized: Invalid share URL for this collection',
                status=401
            )
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(CollectionDetailView, self).get_context_data(*args, **kwargs)

        context.update({
        })
        return context


class CollectionDetailEmbedView(CollectionDetailView):
    template_name = 'composition/collection_detail_embed.html'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        return super(CollectionDetailEmbedView, self).get(request, *args, **kwargs)
