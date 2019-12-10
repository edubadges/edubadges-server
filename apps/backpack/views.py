from backpack.models import BackpackCollection
from django.http import Http404
from django.urls import reverse
from django.views.generic import RedirectView
from issuer.models import BadgeInstance


class RedirectSharedCollectionView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        share_hash = kwargs.get('share_hash', None)
        if not share_hash:
            raise Http404

        try:
            collection = BackpackCollection.cached.get_by_slug_or_entity_id_or_id(share_hash)
        except BackpackCollection.DoesNotExist:
            raise Http404
        return collection.public_url


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
        badgeinstance = None
        share_hash = kwargs.get('share_hash', None)
        if not share_hash:
            raise Http404

        try:
            badgeinstance = BadgeInstance.cached.get_by_slug_or_entity_id_or_id(share_hash)
        except BadgeInstance.DoesNotExist:
            pass

        if not badgeinstance:
            # legacy badge share redirects need to support lookup by pk
            try:
                badgeinstance = BadgeInstance.cached.get(pk=share_hash)
            except (BadgeInstance.DoesNotExist, ValueError):
                pass

        if not badgeinstance:
            raise Http404

        return badgeinstance.public_url

