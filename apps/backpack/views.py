from django.core.urlresolvers import reverse
from django.http import Http404
from django.views.generic import RedirectView


class RedirectSharedCollectionView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        share_hash = kwargs.get('share_hash', None)
        return reverse('collection_json', kwargs={'entity_id': share_hash})


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
