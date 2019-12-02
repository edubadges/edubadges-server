import os
from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.decorators import list_route
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from badgeuser.models import BadgeUser, EmailAddress
from issuer.models import Issuer, IssuerStaff, BadgeClass
from lti_edu.models import LtiPayload, StudentsEnrolled, LtiClient, ResourceLinkBadge
from lti_edu.serializers import StudentsEnrolledSerializer, LTIrequestSerializer, BadgeClassSerializer

# you can override the lti frontend if required
LTI_FRONTEND_URL = os.environ.get('LTI_FRONTEND_URL', 'http://159.65.195.36')


class LtiViewSet(mixins.CreateModelMixin,
                 mixins.ListModelMixin,
                 GenericViewSet):
    """
        LTI integration, now into Canvas
        - POST: enter payload and re-direct to frontend
    """

    permission_classes = [AllowAny]
    queryset = StudentsEnrolled.objects.all()
    serializer_class = LTIrequestSerializer
    authentication_classes = [TokenAuthentication]

    def list(self, request, *args, **kwargs):
        return Response('OK', status=200)

    def create(self, request, *args, **kwargs):

        # show data, only in debug
        if settings.DEBUG:
            print('>> Request data')
            for key, item in list(request.data.items()):
                print(('-- %s > %s' % (key, item)))

        # - oauth_consumer_key should match user
        try:
            client = LtiClient.objects.get(consumer_key=request.data.get('oauth_consumer_key', ''), is_active=True)
        except LtiClient.DoesNotExist:
            return Response({'error': 'Sorry. Could you contact your administrator? The LTI client key not found'},
                            status=403)

        # Check integration
        for field in ['user_id', 'lis_person_name_given', 'lis_person_name_family', 'lis_person_contact_email_primary']:
            if field not in request.data:
                msg = 'Sorry. Could you contact your admin? The LTI Field not found, set privacy correctly, %s' % field
                return Response({'error': msg}, status=403)

        # a. User: if staff, get or create user with data
        roles = request.data.get('roles', '')
        role = 'editor' if ('Instructor' in roles or 'Administrator' in roles) else 'student'

        email = request.data['lis_person_contact_email_primary']
        first_name = request.data['lis_person_name_given']
        last_name = request.data['lis_person_name_family']

        if role == 'student':
            user, token = None, ""
        else:
            lti_id = request.data.get('user_id', None)
            try:
                # see if the user exists with the user_id
                user = BadgeUser.objects.get(lti_id=lti_id)
            except BadgeUser.DoesNotExist:
                # create new user with data from LTI
                defaults = {'first_name': first_name, 'last_name': last_name}
                user, created = BadgeUser.objects.get_or_create(email=email, defaults=defaults)
                user.lti_id = lti_id
                user.save()

                if created:
                    # setup validated email if user is new
                    EmailAddress.objects.create(email=email, user=user, verified=True, primary=True)

            # b. Token: create token for frontend to be authenticated in api
            token, created = Token.objects.get_or_create(user=user)

        # c. Issuer: get or create issuer from client/token
        issuer = client.issuer

        # d. Staff: if editor, then add to issuer
        if role == 'editor':
            IssuerStaff.objects.get_or_create(issuer=issuer, user=user, defaults={'role': 'editor'})

        # d. BadgeClass: determine badge_class, e.g. course, based on resource_link_id, which is unique per placement.
        resource_link_id = request.data.get('resource_link_id', None)
        badge_class_name = request.data.get('context_title', None)
        try:
            resource = ResourceLinkBadge.objects.get(issuer=issuer, resource_link=resource_link_id)
            badge_class = resource.badge_class
            entity_id = badge_class.entity_id
        except ResourceLinkBadge.DoesNotExist:
            # must select or create one
            entity_id, badge_class = None, None

        # e. Student, if class exists and we are student, check enrollment
        if badge_class and role == 'student':
            try:
                award = StudentsEnrolled.objects.get(badge_class=badge_class, email=email)
                consent_given, assertion_slug = award.date_consent_given is not None, award.assertion_slug
            except StudentsEnrolled.DoesNotExist:
                consent_given, assertion_slug = False, ''
        else:
            consent_given, assertion_slug = False, ''

        # ==> Return redirect to frontend with url encoded params
        params = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'token': token,
            'role': role,
            'consent_given': consent_given,
            'issuer_slug': issuer.entity_id,
            'resource_link_id': resource_link_id,
            'badge_class_slug': entity_id,
            'badge_class_name': badge_class_name,
            'assertion_slug': assertion_slug,
        }

        # save data
        LtiPayload.objects.create(data={'request': request.data, 'params': params})

        location = '%s?%s' % (LTI_FRONTEND_URL, urlencode(params))
        res = HttpResponse(location, status=302)
        res['Location'] = location

        if settings.DEBUG:
            print(('---> redirecting to location: %s' % location))
        return res

    @list_route(methods=['POST'], permission_classes=[AllowAny])
    def give_consent(self, request, *args, **kwargs):
        # explicitly give consent as student, allowAny because student's don't have tokens

        for field in ['badge_class_slug', 'email']:
            if field not in request.data:
                return Response(data='field missing', status=401)

        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badge_class_slug'])

        # document that consent was given, update date and name if required.
        defaults = {'date_consent_given': timezone.now(),
                    'first_name': request.data.get('first_name', ''), 'last_name': request.data.get('last_name', '')}
        StudentsEnrolled.objects.update_or_create(
            badge_class=badge_class, email=request.data['email'], defaults=defaults)

        return Response(data='OK', status=200)

    @list_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def get_badges(self, request, *args, **kwargs):

        # get all badgeclasses of the issuer
        issuer = get_object_or_404(Issuer, entity_id=request.data.get('issuer_slug', -1))

        # get students in underlying data, paginate if required
        queryset = BadgeClass.objects.filter(issuer=issuer)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BadgeClassSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BadgeClassSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def link_badge(self, request, *args, **kwargs):

        # link badge_entity_id with resource_id
        resource_link_id = request.data.get('resource_link_id', None)
        if not resource_link_id:
            return Response({'error': 'Sorry. Could you contact your admin? "resource_link_id" is missing'}, status=403)

        badge_class = get_object_or_404(BadgeClass, entity_id=request.data.get('badge_class_slug', -1))
        issuer = get_object_or_404(Issuer, entity_id=request.data.get('issuer_slug', -1))
        ResourceLinkBadge.objects.get_or_create(badge_class=badge_class, issuer=issuer, resource_link=resource_link_id)
        return Response('OK')

    @list_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def get_students(self, request, *args, **kwargs):
        # get students that have enrolled, i.e. given consent.
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data.get('badge_class_slug', -1))

        # get students in underlying data, paginate if required
        queryset = self.queryset.filter(badge_class=badge_class)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = StudentsEnrolledSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StudentsEnrolledSerializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['POST'], permission_classes=[IsAuthenticated])
    def award(self, request, *args, **kwargs):
        # convenience endpoint to document in LTI that student has been awarded
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data.get('badge_class_slug', -1))
        StudentsEnrolled.objects \
            .filter(badge_class=badge_class, email=request.data.get('email', '-1')) \
            .update(date_awarded=timezone.now(), assertion_slug=request.data.get('assertion_slug', ''))
        return Response(data='OK', status=200)
