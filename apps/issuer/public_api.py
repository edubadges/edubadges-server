from django.shortcuts import redirect

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .api import AbstractIssuerAPIEndpoint
from .models import Issuer, BadgeClass, BadgeInstance
import utils
import badgrlog

logger = badgrlog.BadgrLogger()


class JSONComponentView(AbstractIssuerAPIEndpoint):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)

    def log(self, obj):
        pass

    def get(self, request, slug):
        try:
            current_object = self.model.cached.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            self.log(current_object)
            return Response(current_object.json)


class ComponentPropertyDetailView(APIView):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)

    def log(self, obj):
        pass

    def get(self, request, slug):
        try:
            current_object = self.model.cached.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            self.log(current_object)
            return redirect(getattr(current_object, self.prop).url)


class IssuerJson(JSONComponentView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer

    def log(self, obj):
        logger.event(badgrlog.IssuerRetrievedEvent(obj, self.request))


class IssuerImage(ComponentPropertyDetailView):
    """
    GET an image that represents an Issuer
    """
    model = Issuer
    prop = 'image'

    def log(self, obj):
        logger.event(badgrlog.IssuerImageRetrievedEvent(obj, self.request))


class BadgeClassJson(JSONComponentView):
    """
    GET the actual OBI badge object for a badgeclass via public/badges/:slug endpoint
    """
    model = BadgeClass

    def log(self, obj):
        logger.event(badgrlog.BadgeClassRetrievedEvent(obj, self.request))


class BadgeClassImage(ComponentPropertyDetailView):
    """
    GET the unbaked badge image from a pretty url instead of media path
    """
    model = BadgeClass
    prop = 'image'

    def log(self, obj):
        logger.event(badgrlog.BadgeClassImageRetrievedEvent(obj, self.request))


class BadgeClassCriteria(ComponentPropertyDetailView):
    model = BadgeClass
    prop = 'criteria'
    queryset = BadgeClass.objects.all()

    def get(self, request, slug):
        # TODO: Improve rendered HTML view template.
        current_query = self.queryset.filter(slug=slug)

        if not current_query.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        current_object = current_query[0]

        logger.event(badgrlog.BadgeClassCriteriaRetrievedEvent(current_object, request))

        if current_object.criteria_text is None or current_object.criteria_text == "":
            return redirect(current_object.criteria_url)

        return Response(current_object.criteria_text)


class BadgeInstanceJson(JSONComponentView):
    model = BadgeInstance

    def get(self, request, slug):
        try:
            current_object = self.model.cached.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if current_object.revoked is False:

                logger.event(badgrlog.BadgeAssertionCheckedEvent(current_object, request))
                return Response(current_object.json)
            else:
                # TODO update terms based on final accepted terms in response to
                # https://github.com/openbadges/openbadges-specification/issues/33
                revocation_info = {
                    '@context': utils.CURRENT_OBI_CONTEXT_IRI,
                    'id': current_object.get_full_url(),
                    'revoked': True,
                    'revocationReason': current_object.revocation_reason
                }

                logger.event(badgrlog.RevokedBadgeAssertionCheckedEvent(current_object, request))
                return Response(revocation_info, status=status.HTTP_410_GONE)


class BadgeInstanceImage(ComponentPropertyDetailView):
    model = BadgeInstance
    prop = 'image'

    def log(self, badge_instance):
        logger.event(badgrlog.BadgeInstanceDownloadedEvent(badge_instance, self.request))

    def get(self, request, slug):
        try:
            current_object = self.model.cached.get(slug=slug, revoked=False)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            self.log(current_object)
            return redirect(getattr(current_object, self.prop).url)

