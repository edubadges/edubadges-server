from django.http import Http404
from django.views.generic import RedirectView
from issuer.models import BadgeInstance


class LegacyBadgeShareRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        entity_id = kwargs.get('entity_id', None)
        if not entity_id:
            raise Http404
        try:
            badgeinstance = BadgeInstance.objects.get(entity_id=entity_id)
            return badgeinstance.public_url
        except BadgeInstance.DoesNotExist:
            raise Http404

