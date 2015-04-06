# Views for Issuer API endpoints (incoming requests to this application)
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.utils.text import slugify
from django.shortcuts import redirect

from rest_framework import status, authentication, permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from mainsite.renderers import JSONLDRenderer
from models import EarnerNotification, Issuer, IssuerBadgeClass, IssuerAssertion
from serializers import EarnerNotificationSerializer, IssuerSerializer, IssuerBadgeClassSerializer, IssuerAssertionSerializer
import utils


class EarnerNotificationList(APIView):
    """
    Deprecated: Earner notifications allow a user to send email notifications about badges issued on other platforms.
    """
    model = EarnerNotification

    def get(self, request):
        """
        Depreated: GET a list of all earner notifications in the system.
        """
        try:
            notifications = EarnerNotification.objects.all()
        except EarnerNotification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EarnerNotificationSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Deprecated: Create a new EarnerNotification as long as you know the right email address for the badge
        assertion, and the earner has not been previously notified.
        ---
        parameters:
            - name: url
              description: The URL of a hosted assertion you wish to notify an earner about.
              type: string
              paramType: form
            - name: email
              description: The email address of the badge recipient. Must match the assertion.
              type: string
              paramType: form
        """
        data = {'url': request.data.get('url'), 'email': request.data.get('email')}
        serializer = EarnerNotificationSerializer(data=data)

        if serializer.is_valid():
            try:
                serializer.create()
            except Exception as e:
                return Response(e.message, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EarnerNotificationDetail(APIView):
    model = EarnerNotification

    def get(self, request):
        raise NotImplementedError("Earner notidication detail not implemented.")


class IssuerList(APIView):
    """
    Issuer List resource for the authenticated user
    """
    model = Issuer
    serializer_class = IssuerSerializer

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get(self, request):
        """
        GET a list of issuers owned, edited or staffed by the logged in user
        ---
        serializer: IssuerSerializer
        """
        if not isinstance(request.user, get_user_model()):
            # TODO consider changing this a public API of all issuers (that are public?)
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the Issuers this user owns, edits, or staffs:
        user_issuers = Issuer.objects.filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id) |
            Q(staff__id=request.user.id)
        )
        if not user_issuers.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = IssuerSerializer(user_issuers, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """
        Define a new issuer to be owned by the logged in user
        ---
        parameters:
            - name: name
              description: The name of the Issuer
              required: true
              type: string
              paramType: form
            - name: description
              description: A short text description of the new Issuer
              required: true
              type: string
              paramType: form
            - name: url
              description: A fully-qualified URL of the Issuer's website or homepage
              required: true
              type: string
              paramType: form
            - name: email
              description: A contact email for the Issuer
              required: true
              type: string
              paramType: form
            - name: image
              description: An image file that represents the Issuer, such as a logo
              required: false
              type: file
              paramType: form
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = IssuerSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Pass in user values where we have a real user object instead of a url
        # and non-model-field data to go into badge_object
        serializer.save(
            owner=request.user,
            created_by=request.user
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IssuerDetail(APIView):
    """
    GET details on one issuer. PUT and DELETE should be highly restricted operations and are not implemented yet
    """
    model = Issuer
    serializer_class = IssuerSerializer
    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get(self, request, slug):
        """
        Detail view for one issuer owned, edited, or staffed by the authenticated user
        ---
        serializer: IssuerSerializer
        """
        try:
            current_issuer = Issuer.objects.get(slug=slug)
        except Issuer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = IssuerSerializer(current_issuer, context={'request': request})
            return Response(serializer.data)


class BadgeClassList(APIView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = IssuerBadgeClass

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get(self, request, issuerSlug):
        """
        GET a list of badgeclasses within one Issuer context.
        Authenticated user must have owner, editor, or staff status on Issuer
        ---
        serializer: IssuerBadgeClassSerializer
        """
        if not isinstance(request.user, get_user_model()):
            # TODO consider changing this a public API of all issuers (that are public?)
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Ensure current user has permissions on current issuer
        current_issuer = Issuer.objects.filter(
            slug=issuerSlug
        ).filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id) |
            Q(staff__id=request.user.id)
        ).select_related('badgeclasses')[0]

        # Get the Issuers this user owns, edits, or staffs:
        issuer_badge_classes = current_issuer.badgeclasses.all()

        if not issuer_badge_classes.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = IssuerBadgeClassSerializer(issuer_badge_classes, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, issuerSlug):
        """
        Define a new BadgeClass to be owned by a particular Issuer.
        Authenticated user must have owner or editor status on Issuer
        ('staff' status is inadequate)
        ---
        serializer: IssuerBadgeClassSerializer
        parameters:
            - name: issuerSlug
              required: true
              type: string
              paramType: path
              description: slug of the Issuer to be owner of the new BadgeClass
            - name: name
              required: true
              type: string
              paramType: form
              description: A short name for the new BadgeClass
            - name: slug
              required: false
              type: string
              paramType: form
              description: Optionally customizable slug. Otherwise generated from name
            - name: image
              type: file
              required: true
              paramType: form
              description: An image to represent the BadgeClass. Must be a square PNG with no existing OBI assertion data baked into it.
            - name: criteria
              type: string
              required: true
              paramType: form
              description: Either a URL of a remotely hosted criteria page or a text string describing the criteria.
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Step 1: Locate the issuer
        current_issuer = current_issuer = Issuer.objects.filter(
            slug=issuerSlug
        ).filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id)
        )

        if not current_issuer.exists():
            return Response('Issuer not found, or improper permissions on issuer', status=status.HTTP_404_NOT_FOUND)

        current_issuer = current_issuer[0]

        # Step 2: validate, create new Badge Class
        serializer = IssuerBadgeClassSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        serializer.save(
            issuer=current_issuer,
            created_by=request.user,
            description=request.data.get('description')
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BadgeClassDetail(APIView):
    """
    GET details on one BadgeClass. PUT and DELETE should be restricted to BadgeClasses that haven't been issued yet.
    """
    model = IssuerBadgeClass

    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get(self, request, issuerSlug, badgeSlug):
        """
        GET single BadgeClass representation
        ---
        serializer: IssuerBadgeClassSerializer
        """
        # TODO long term: allow GET if issuer has permission to issue even if not creator

        try:
            current_badgeclass = IssuerBadgeClass.objects.get(slug=badgeSlug, issuer__slug=issuerSlug)
        except IssuerBadgeClass.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = IssuerBadgeClassSerializer(current_badgeclass, context={'request': request})
            return Response(serializer.data)

    def delete(self, request, issuerSlug, badgeSlug):
        """
        DELETE a badge class that has never been issued. This will fail if any assertions exist for the BadgeClass.
        Restricted to owners or editors (not staff) of the corresponding Issuer.
        ---
        responseMessages:
            - code: 400
              message: Badge Class either couldn't be deleted. It may have already been issued, or it may already not exist.
            - code: 200
              message: Badge has been deleted.
        """

        current_badgeclass = IssuerBadgeClass.objects.filter(
            slug=badgeSlug,
            issuer__slug=issuerSlug,
            assertions=None
        ). filter(
            Q(issuer__owner__id=request.user.id) |
            Q(issuer__editors__id=request.user.id)
        )

        if current_badgeclass.exists():
            current_badgeclass[0].delete()
        else:
            return Response(
                "Badge Class either couldn't be deleted. It may have already been issued, or it may already not exist.",
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response("Badge " + badgeSlug + " has been deleted.", status.HTTP_200_OK)


class AssertionList(APIView):
    """
    GET a list of assertions per issuer & per badgeclass
    POST to issue a new assertion
    """
    model = IssuerAssertion
    serializer_class = IssuerAssertionSerializer
    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def post(self, request, issuerSlug, badgeSlug):
        """
        Issue a badge to a single recipient.
        ---
        serializer: IssuerAssertionSerializer
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Ensure current user has permissions on current badgeclass
        current_badgeclass = IssuerBadgeClass.objects.filter(
            slug=badgeSlug
        ).filter(
            Q(issuer__owner__id=request.user.id) |
            Q(issuer__editors__id=request.user.id) |
            Q(issuer__staff__id=request.user.id)
        ).select_related('issuers')
        if current_badgeclass.exists():
            current_badgeclass = current_badgeclass[0]

        serializer = IssuerAssertionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        serializer.save(
            issuer=current_badgeclass.issuer,
            badgeclass=current_badgeclass,
            created_by=request.user
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, issuerSlug, badgeSlug):
        """
        Get a list of all issued assertions for a single BadgeClass.
        ---
        serializer: IssuerAssertionSerializer
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Ensure current user has permissions on current badgeclass
        current_badgeclass = IssuerBadgeClass.objects.filter(
            slug=badgeSlug
        ).filter(
            Q(issuer__owner__id=request.user.id) |
            Q(issuer__editors__id=request.user.id) |
            Q(issuer__staff__id=request.user.id)
        ).select_related('assertions')
        if current_badgeclass.exists():
            current_badgeclass = current_badgeclass[0]

        # Get the Issuers this user owns, edits, or staffs:
        assertions = current_badgeclass.assertions.all()

        if not assertions.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = IssuerAssertionSerializer(assertions, many=True, context={'request': request})
        return Response(serializer.data)


class AssertionDetail(APIView):
    """
    Endpoints for (GET)ting a single assertion or revoking a badge (DELETE)
    """
    model = IssuerAssertion

    def get(self, request, issuerSlug, badgeSlug, assertionSlug):
        """
        GET a single assertion's details.
        The assertionSlug URL prameter is the only one that varies the request,
        but the assertion must belong to an issuer owned, edited, or staffed by the
        authenticated user.
        ---
        serializer: IssuerAssertionSerializer
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        current_assertion = IssuerAssertion.objects.filter(
            slug=assertionSlug
        ).filter(
            Q(issuer__owner__id=request.user.id) |
            Q(issuer__editors__id=request.user.id) |
            Q(issuer__staff__id=request.user.id)
        )
        if current_assertion.exists():
            current_assertion = current_assertion[0]
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = IssuerAssertionSerializer(current_assertion, context={'request': request})

        return Response(serializer.data)

    def delete(self, request, issuerSlug, badgeSlug, assertionSlug):
        """
        Revoke an issued badge assertion.
        Limited to Issuer owner and editors (not staff)
        ---
        parameters:
            - name: revocation_reason
              description: A short description of why the badge is to be revoked
              required: true
              type: string
              paramType: form
        responseMessages:
            - code: 200
              message: Assertion has been revoked.
            - code: 400
              message: Assertion is already revoked
            - code: 404
              message: Assertion not found or user has inadequate permissions.
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        if request.data.get('revocation_reason') is None:
            raise ValidationError("revocation_reason is required to revoke a badge assertion")

        current_assertion = IssuerAssertion.objects.filter(
            slug=assertionSlug
        ).filter(
            Q(issuer__owner__id=request.user.id) |
            Q(issuer__editors__id=request.user.id)
        )
        if current_assertion.exists():
            current_assertion = current_assertion[0]
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if current_assertion.revoked is True:
            return Response("Assertion is already revoked.", status=status.HTTP_400_BAD_REQUEST)

        current_assertion.revoked = True
        current_assertion.revocation_reason = request.data.get('revocation_reason')
        current_assertion.image.delete()
        current_assertion.save()

        return Response(
            "Assertion {} has been revoked.".format(current_assertion.slug),
            status=status.HTTP_200_OK
        )




""" <<<<<<<<<<<<<<<<<<<<<<< PUBLIC API >>>>>>>>>>>>>>>>>>>>>>>>>
Public Open Badges Resources
TODO: move this to its own file.
"""
# Abstract badge object
class JSONBadgeObjectView(APIView):
    renderer_classes = (JSONRenderer, JSONLDRenderer)

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

    def get(self, request, slug):
        try:
            current_badgeclass = IssuerBadgeClass.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return redirect(current_badgeclass.image.url)


class IssuerBadgeClassCriteria(APIView):
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

    def get(self, request, slug):
        try:
            current_assertion = IssuerAssertion.objects.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return redirect(current_assertion.image.url)
