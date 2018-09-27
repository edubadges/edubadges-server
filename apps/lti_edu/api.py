# from entity.api import BaseEntityListView
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from issuer.permissions import BadgrOAuthTokenHasEntityScope
from lti_edu.models import StudentsEnrolled
from lti_edu.serializers import StudentsEnrolledSerializer
from lti_edu.views import LtiViewSet
from issuer.models import BadgeClass

class LTIStudentsEnrolledDetail(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer
    
    def post(self, request, **kwargs):
        
        for field in ['badgeclass_slug', 'edu_id']:
            if field not in request.data:
                return Response(data='field missing', status=401)

        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])

        # implicit consent given by enrolling?
        defaults = {'date_consent_given': timezone.now(),
                    'first_name': request.data.get('first_name', ''), 
                    'last_name': request.data.get('last_name', '')}
        
        # check if not already enrolled
        try:
            StudentsEnrolled.objects.get(edu_id=request.data['edu_id'], 
                                         badge_class_id=badge_class.pk)
            return Response(data='already enrolled', status=200)
        except StudentsEnrolled.DoesNotExist:
            StudentsEnrolled.objects.update_or_create(
                badge_class=badge_class, email=request.data['email'], 
                edu_id=request.data['edu_id'], defaults=defaults)
            return Response(data='OK', status=200)
 