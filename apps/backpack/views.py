from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import DetailView
from django.views.generic import RedirectView

from backpack.models import BackpackCollection


class SharedCollectionView(DetailView):
    template_name = 'public/shared_collection.html'
    model = BackpackCollection
    context_object_name = 'collection'
    slug_url_kwarg = 'share_hash'
    slug_field = 'share_hash'

    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        response = super(SharedCollectionView, self).get(request, *args, **kwargs)

        if self.object.share_hash == '' or \
                self.object.share_hash != kwargs.get('share_hash'):
            return HttpResponse(
                'Unauthorized: Invalid share URL for this collection',
                status=401
            )
        return response

    def get_context_data(self, *args, **kwargs):
        context = super(SharedCollectionView, self).get_context_data(*args, **kwargs)

        context.update({
            'badges': self.object.cached_badgeinstances()
        })
        return context


class EmbeddedSharedCollectionView(SharedCollectionView):
    @method_decorator(xframe_options_exempt)
    def get(self, request, *args, **kwargs):
        return super(EmbeddedSharedCollectionView, self).get(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super(EmbeddedSharedCollectionView, self).get_context_data(*args, **kwargs)
        context.update({
            'embedded': True
        })
        return context


class LegacyCollectionShareRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        new_pattern_name = self.request.resolver_match.url_name.replace('legacy_','')
        kwargs.pop('pk')
        url = reverse(new_pattern_name, args=args, kwargs=kwargs)
        return url


class LegacyBadgeShareRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        entity_id = kwargs.get('share_hash', None)
        if not entity_id:
            raise Http404
        return reverse('badgeinstance_json', kwargs={'entity_id': entity_id})
