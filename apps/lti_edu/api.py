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
from entity.api import BaseEntityListView


class LTICheckIfStudentIsEnrolled(BaseEntityListView):
    
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer
    
    def post(self, request, **kwargs):
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])
        try:
            StudentsEnrolled.objects.get(edu_id=request.data['edu_id'], 
                                         badge_class_id=badge_class.pk)
            return Response(data='alreadyEnrolled', status=200)
        except StudentsEnrolled.DoesNotExist:
            return Response(data='notEnrolled', status=200)
        

class LTIStudentsEnrolledDetail(BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer
    
    def get_objects(self, request, **kwargs):
        badge_class = get_object_or_404(BadgeClass, entity_id=kwargs['badgeclass_slug'])
        return StudentsEnrolled.objects.filter(badge_class_id=badge_class.pk)
    
    def post(self, request, **kwargs):
        
        for field in ['badgeclass_slug', 'edu_id']:
            if field not in request.data:
                return Response(data='field missing', status=401)

        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])

        # consent given when enrolling
        defaults = {'date_consent_given': timezone.now(),
                    'first_name': request.data.get('first_name', ''), 
                    'last_name': request.data.get('last_name', '')}
        
        # check if not already enrolled
        try:
            StudentsEnrolled.objects.get(edu_id=request.data['edu_id'], 
                                         badge_class_id=badge_class.pk)
            return Response(data='alreadyEnrolled', status=200)
        except StudentsEnrolled.DoesNotExist:
            StudentsEnrolled.objects.update_or_create(
                badge_class=badge_class, email=request.data['email'], 
                edu_id=request.data['edu_id'], defaults=defaults)
            return Response(data='enrolled', status=200)
        
    def get(self, request, **kwargs):
        if 'badgeclass_slug' not in kwargs:
            return Response(data='field missing', status=500)
        return super(LTIStudentsEnrolledDetail, self).get(request, **kwargs) 
 