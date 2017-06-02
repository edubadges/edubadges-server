from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView
from django.views.generic import RedirectView
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from composition.models import Collection, LocalBadgeInstance
from composition.utils import get_badge_by_identifier
from issuer.models import BadgeInstance
from issuer.public_api import JSONComponentView
from issuer.renderers import BadgeInstanceHTMLRenderer
from issuer.utils import CURRENT_OBI_CONTEXT_IRI, CURRENT_OBI_VERSION
from mainsite.utils import OriginSetting


class SharedBadgeView(JSONComponentView):
    renderer_classes = (JSONRenderer, BadgeInstanceHTMLRenderer,)
    html_renderer_class = BadgeInstanceHTMLRenderer

    def get_object(self, queryset=None):
        badge = get_badge_by_identifier(self.kwargs.get('badge_id'))
        if badge is None:
            raise BadgeInstance.DoesNotExist("No badge matching the specified sharing identifier")
        return badge

    def get_renderer_context(self, **kwargs):
        context = super(SharedBadgeView, self).get_renderer_context(**kwargs)
        if hasattr(self, 'badge'):
            if isinstance(self.badge, LocalBadgeInstance):
                context['badgeclass_image_png'] = "{}{}?type=png".format(OriginSetting.HTTP,reverse('localbadgeinstance_image', kwargs={'slug': self.badge.slug}))
            elif isinstance(self.badge, BadgeInstance):
                context['badgeclass_image_png'] = "{}{}?type=png".format(OriginSetting.HTTP,reverse('badgeclass_image', kwargs={'slug': self.badge.cached_badgeclass.slug}))
            context.update({
                'badge_instance': self.badge,
                'badge_class': self.badge.cached_badgeclass,
                'issuer': self.badge.cached_issuer,
            })
        context['obi_version'] = self._get_request_obi_version(self.request)
        return context

    def get(self, request, badge_id, format='html'):
        try:
            self.badge = self.get_object(badge_id)
        except BadgeInstance.DoesNotExist as e:
            return Response(e.message, status=status.HTTP_404_NOT_FOUND)

        if self.badge.revoked:
            revocation_info = {
                '@context': CURRENT_OBI_CONTEXT_IRI,
                'id': self.badge.jsonld_id,
                'revoked': True,
                'revocationReason': self.badge.revocation_reason
            }
            return Response(revocation_info, status=status.HTTP_410_GONE)

        return Response(self.badge.get_json(obi_version=self._get_request_obi_version(request)))


class CollectionDetailView(DetailView):
    template_name = 'public/shared_collection.html'
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
            'badges': self.object.badges.all()
        })
        return context


class CollectionDetailEmbedView(CollectionDetailView):
    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        return super(CollectionDetailEmbedView, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(CollectionDetailEmbedView, self).get_context_data(*args, **kwargs)
        context.update({
            'embedded': True
        })
        return context


class LegacyCollectionShareRedirectView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        new_pattern_name = self.request.resolver_match.url_name.replace('legacy_','')
        kwargs.pop('pk')
        url = reverse(new_pattern_name, args=args, kwargs=kwargs)
        return url
