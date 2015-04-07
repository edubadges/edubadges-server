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


"""
Abstract Badge Object View Classes:
"""
class JSONBadgeObjectView(AbstractIssuerAPIEndpoint):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        try:
            current_object = self.model.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(current_object.badge_object)


class BadgePropertyDetailView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, slug):
        current_query = self.queryset.filter(slug=slug)
        if not current_query.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        current_object = current_query[0]
        return redirect(getattr(current_object, self.prop).url)


"""
Public views for Open Badges Issuer Objects and associated Resources
"""
class IssuerBadgeObject(JSONBadgeObjectView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer


class IssuerImage(BadgePropertyDetailView):
    """
    GET an image that represents an Issuer
    """
    model = Issuer
    prop = 'image'
    Issuer.objects.exclude(image=None)


#Badge Class views
class IssuerBadgeClassObject(JSONBadgeObjectView):
    """
    GET the actual OBI badge object for a badgeclass via public/badges/:slug endpoint
    """
    model = IssuerBadgeClass


class IssuerBadgeClassImage(BadgePropertyDetailView):
    """
    GET the unbaked badge image from a pretty url instead of media path
    """
    model = IssuerBadgeClass
    prop = 'image'
    queryset = IssuerBadgeClass.objects.exclude(image=None)


class IssuerBadgeClassCriteria(BadgePropertyDetailView):
    model = IssuerBadgeClass
    prop = 'criteria'
    queryset = IssuerBadgeClass.objects.all()

    def get(self, request, slug):
        # TODO: Improve rendered HTML view template.
        current_query = self.queryset.filter(slug=slug)

        if not current_query.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        current_object = current_query[0]
        if current_object.criteria_text is None or current_object.criteria_text == "":
            return redirect(current_object.criteria_url)

        return Response(current_object.criteria_text)


# Assertion views
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


class IssuerAssertionImage(BadgePropertyDetailView):
    model = IssuerAssertion
    prop = 'image'
    queryset = IssuerAssertion.objects.filter(revoked=False)
