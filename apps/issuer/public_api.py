# Views for Issuer API endpoints (incoming requests to this application)
from django.shortcuts import redirect

from rest_framework import status, authentication, permissions
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from mainsite.renderers import JSONLDRenderer
from models import Issuer, IssuerBadgeClass, IssuerAssertion
import utils
from api import AbstractIssuerAPIEndpoint

"""
Public Open Badges Resources
"""
# Abstract badge object
class JSONBadgeObjectView(AbstractIssuerAPIEndpoint):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        try:
            current_object = self.model.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(current_object.badge_object)


class IssuerBadgeObject(JSONBadgeObjectView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer


class IssuerBadgeClassObject(JSONBadgeObjectView):
    """
    GET the actual OBI badge object for a badgeclass via public/badges/:slug endpoint
    """
    model = IssuerBadgeClass


class IssuerBadgeClassImage(APIView):
    """
    GET the unbaked badge image from a pretty url instead of media path
    """
    model = IssuerBadgeClass
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        try:
            current_badgeclass = IssuerBadgeClass.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return redirect(current_badgeclass.image.url)


class IssuerBadgeClassCriteria(AbstractIssuerAPIEndpoint):
    model = IssuerBadgeClass

    def get(self, request, slug):
        # TODO: This view will display an HTML template if the badgeclass has criteria_text,
        # or will 301 redirect to criteria_url
        return NotImplementedError("Criteria view not implemented.")


class IssuerAssertionBadgeObject(JSONBadgeObjectView):
    model = IssuerAssertion

    def get(self, request, slug):
        try:
            current_object = self.model.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            if current_object.revoked is False:
                return Response(current_object.badge_object)
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


class IssuerAssertionImage(APIView):
    model = IssuerAssertion
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        try:
            current_assertion = IssuerAssertion.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return redirect(current_assertion.image.url)
