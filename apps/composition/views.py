from django.core.urlresolvers import reverse
from django.http import Http404
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView
from django.views.generic import RedirectView

from composition.models import Collection
from composition.utils import get_badge_by_identifier
from issuer.utils import obscure_email_address


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
