from django.shortcuts import redirect

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .api import AbstractIssuerAPIEndpoint
from .models import Issuer, BadgeClass, BadgeInstance
import utils


class JSONComponentView(AbstractIssuerAPIEndpoint):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        try:
            current_object = self.model.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(current_object.json)


class ComponentPropertyDetailView(APIView):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        current_query = self.queryset.filter(slug=slug)
        if not current_query.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        current_object = current_query[0]
        return redirect(getattr(current_object, self.prop).url)


class IssuerJson(JSONComponentView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer


class IssuerImage(ComponentPropertyDetailView):
    """
    GET an image that represents an Issuer
    """
    model = Issuer
    prop = 'image'
    Issuer.objects.exclude(image=None)


class BadgeClassJson(JSONComponentView):
    """
    GET the actual OBI badge object for a badgeclass via public/badges/:slug endpoint
    """
    model = BadgeClass


class BadgeClassImage(ComponentPropertyDetailView):
    """
    GET the unbaked badge image from a pretty url instead of media path
    """
    model = BadgeClass
    prop = 'image'
    queryset = BadgeClass.objects.exclude(image=None)


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
        if current_object.criteria_text is None or current_object.criteria_text == "":
            return redirect(current_object.criteria_url)

        return Response(current_object.criteria_text)


class BadgeInstanceJson(JSONComponentView):
    model = BadgeInstance

    def get(self, request, slug):
        try:
            current_object = self.model.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if current_object.revoked is False:
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
                return Response(revocation_info, status=status.HTTP_410_GONE)


class BadgeInstanceImage(ComponentPropertyDetailView):
    model = BadgeInstance
    prop = 'image'
    queryset = BadgeInstance.objects.filter(revoked=False)
