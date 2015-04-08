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
from serializers import EarnerNotificationSerializer, IssuerSerializer, IssuerBadgeClassSerializer, IssuerAssertionSerializer, IssuerRoleActionSerializer
import utils

from badgeuser.serializers import UserProfileField


class AbstractIssuerAPIEndpoint(APIView):
    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)


class IssuerList(AbstractIssuerAPIEndpoint):
    """
    Issuer List resource for the authenticated user
    """
    model = Issuer
    serializer_class = IssuerSerializer

    def get(self, request):
        """
        GET a list of issuers owned, edited or staffed by the logged in user
        ---
        serializer: IssuerSerializer
        """

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

        serializer = IssuerSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Pass in user values where we have a real user object instead of a url
        # and non-model-field data to go into badge_object
        serializer.save(
            owner=request.user,
            created_by=request.user
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IssuerDetail(AbstractIssuerAPIEndpoint):
    """
    GET details on one issuer. PUT and DELETE should be highly restricted operations and are not implemented yet
    """
    model = Issuer
    serializer_class = IssuerSerializer

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


class IssuerRoleList(AbstractIssuerAPIEndpoint):
    model = Issuer

    def get(self, request, slug):
        """
        Get a list of users associated with a role on an Issuer
        ---
        type:
          username:
            type: string
          earnerIds:
            type: array
            description: An array of the user's confirmed email addresses
          id:
            type: integer
            description: The user id number
          name:
            type: string
            description: The user's full name
        """

        current_issuer = Issuer.objects.filter(slug=slug).filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id) |
            Q(staff__id=request.user.id)
        ).prefetch_related(self.role)

        if not current_issuer.exists():
            return Response(
                "Issuer %s not found. Authenticated user must have owner, editor or staff rights on the issuer." % slug,
                status=status.HTTP_404_NOT_FOUND
            )

        else:
            if getattr(current_issuer[0], self.role).exists():
                serializer = UserProfileField(getattr(current_issuer[0], self.role).all(), many=True)
                return Response(serializer.data)
            else:
                return Response([], status=status.HTTP_200_OK)

    def post(self, request, slug):
        """
        Add or remove a user from a role on an issuer. Limited to Owner users only.
        ---
        parameters:
            - name: slug
              type: string
              paramType: path
              description: The slug of the issuer whose roles to modify.
              required: true
            - name: action
              type: string
              paramType: form
              description: Must be one of `add` or `remove`
              required: true
            - name: username
              type: string
              paramType: form
              description: The username of the user to add or remove from this role.
              required: true
        type:
          username:
            type: string
          earnerIds:
            type: array
            description: An array of the user's confirmed email addresses
          id:
            type: integer
            description: The user id number
          name:
            type: string
            description: The user's full name
        """

        # validate POST data
        serializer = IssuerRoleActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        current_issuer = Issuer.objects.filter(
            slug=slug,
            owner__id=request.user.id
        ).prefetch_related(self.role)
        user_to_modify = get_user_model().objects.filter(username=request.data.get('username'))

        if not current_issuer.exists():
            return Response(
                "Issuer %s not found. Authenticated user must be Issuer's owner to modify user permissions." % slug,
                status=status.HTTP_404_NOT_FOUND
            )

        if not user_to_modify.exists():
            return Response(
                "User %s not found. Cannot modify Issuer permissions." % serializer.validated_data.get('username'),
                status=status.HTTP_404_NOT_FOUND
            )

        action = request.data.get('action')

        if action == 'add' or action == '':
            getattr(current_issuer[0], self.role).add(user_to_modify[0])
        elif action == 'remove':
            getattr(current_issuer[0], self.role).remove(user_to_modify[0])

        if getattr(current_issuer[0], self.role).exists():
            return Response(UserProfileField(getattr(current_issuer[0], self.role).all(), many=True).data)
        else:
            return Response([], status=status.HTTP_200_OK)


class IssuerEditorsList(IssuerRoleList):
    role = 'editors'


class IssuerStaffList(IssuerRoleList):
    role = 'staff'


class BadgeClassList(AbstractIssuerAPIEndpoint):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = IssuerBadgeClass

    def get(self, request, issuerSlug):
        """
        GET a list of badgeclasses within one Issuer context.
        Authenticated user must have owner, editor, or staff status on Issuer
        ---
        serializer: IssuerBadgeClassSerializer
        """

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


class BadgeClassDetail(AbstractIssuerAPIEndpoint):
    """
    GET details on one BadgeClass. PUT and DELETE should be restricted to BadgeClasses that haven't been issued yet.
    """
    model = IssuerBadgeClass

    def get(self, request, issuerSlug, badgeSlug):
        """
        GET single BadgeClass representation
        ---
        serializer: IssuerBadgeClassSerializer
        """
        # TODO long term: allow GET if issuer has permission to issue even if not creator

        current_badgeclass = IssuerBadgeClass.objects.filter(slug=badgeSlug, issuer__slug=issuerSlug).filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id) |
            Q(staff__id=request.user.id)
        )

        if not current_badgeclass.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        current_badgeclass = current_badgeclass[0]
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


class AssertionList(AbstractIssuerAPIEndpoint):
    """
    GET a list of assertions per issuer & per badgeclass
    POST to issue a new assertion
    """
    model = IssuerAssertion
    serializer_class = IssuerAssertionSerializer

    def post(self, request, issuerSlug, badgeSlug):
        """
        Issue a badge to a single recipient.
        ---
        serializer: IssuerAssertionSerializer
        """

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
        else:
            return Response(
                "Issuer not found or current user lacks permission to issue badges.",
                status=status.HTTP_404_NOT_FOUND
            )

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


class AssertionDetail(AbstractIssuerAPIEndpoint):
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
