import json
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404

from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView, TemplateView
from django.views.generic import RedirectView

from badgeuser.serializers import UserProfileField
from composition.utils import get_badge_by_identifier
from issuer.models import BadgeInstance
from issuer.utils import obscure_email_address
from mainsite.utils import installed_apps_list, OriginSetting

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


class SharedBadgeView(DetailView):
    template_name = 'public/shared_badge.html'
    context_object_name = 'badge'

    def get_object(self, queryset=None):
        badge = get_badge_by_identifier(self.kwargs.get('badge_id'))
        if badge is None:
            raise Http404
        return badge

    def get_context_data(self, **kwargs):
        context = super(SharedBadgeView, self).get_context_data(**kwargs)
        context.update({
            'badge_instance': self.object,
            'badge_class': self.object.cached_badgeclass,
            'issuer': self.object.cached_issuer,
            'badge_instance_image_url': self.object.image.url if self.object.image else None,
            'obscured_recipient': obscure_email_address(self.object.recipient_identifier)
        })
        return context


class CollectionDetailView(DetailView):
    model = Collection
    context_object_name = 'collection'
    slug_url_kwarg = 'share_hash'
    slug_field = 'share_hash'

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


class LegacyCollectionShareRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        new_pattern_name = self.request.resolver_match.url_name.replace('legacy_','')
        kwargs.pop('pk')
        url = reverse(new_pattern_name, args=args, kwargs=kwargs)
        return url
