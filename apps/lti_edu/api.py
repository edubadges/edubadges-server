# from entity.api import BaseEntityListView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST
from mainsite.permissions import AuthenticatedWithVerifiedEmail, MayUseManagementDashboard

from lti_edu.models import StudentsEnrolled, LtiClient
from lti_edu.permissions import IssuerWithinUserScope
from lti_edu.serializers import StudentsEnrolledSerializer, StudentsEnrolledSerializerWithRelations, LtiClientsSerializer
from issuer.models import BadgeClass
from entity.api import BaseEntityListView, BaseEntityDetailView


class CheckIfStudentIsEnrolled(BaseEntityListView):
    """
    POST to check if student is enrolled
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer

    def post(self, request, **kwargs):
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])
        if request.data.get('edu_id'):
            if request.user.may_enroll(badge_class):
                return Response(data='notEnrolled', status=200)
            else:
                return Response(data='enrolled', status=200)
        else:
            return Response(data='noEduID', status=200)


class LtiClientsList(BaseEntityListView):
    """
    GET a list of lti clients within users scope
    POST to create new lti client
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, IssuerWithinUserScope)
    model = LtiClient
    serializer_class = LtiClientsSerializer

    def get_objects(self, request, **kwargs):
        if request.user.has_perm('badgeuser.has_institution_scope'):
            institution_id = request.user.institution.id
            return LtiClient.objects.filter(issuer__faculty__institution_id=institution_id).distinct()
        elif request.user.has_perm('badgeuser.has_faculty_scope'):
            return LtiClient.objects.filter(issuer__faculty__in=request.user.faculty.all()).distinct()
        return LtiClient.objects.none()

    def post(self, request, **kwargs):
        return super(LtiClientsList, self).post(request, **kwargs)



class StudentEnrollmentList(BaseEntityListView):
    """
    GET a list of enrollments for a student
    DELETE to delete enrollment
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializerWithRelations

    def get_objects(self, request, **kwargs):
        recipient_identifier = request.user.get_recipient_identifier()
        return StudentsEnrolled.objects.filter(edu_id=recipient_identifier)

    def get(self, request, **kwargs):
        return super(StudentEnrollmentList, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        enrollment = StudentsEnrolled.objects.get(id=request.data['enrollmentID'])
        if enrollment.date_awarded:
            return Response(data='Awarded enrollments cannot be withdrawn', status=403)
        if request.user.get_recipient_identifier() == enrollment.edu_id:
            enrollment.delete()
            return Response(status=200)
        else:
            return Response(data='Users can only withdraw their own enrollments', status=403)


class StudentsEnrolledList(BaseEntityListView):
    """
    GET: get  list of enrollments for a badgeclass
    POST: to enroll student
    """
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
        if request.user.may_enroll(badge_class):
            enrollment = StudentsEnrolled.objects.create(edu_id=request.data['edu_id'],
                                                        badge_class_id=badge_class.pk,
                                                        email=request.data['email'],
                                                        **defaults)
            return Response(data='enrolled', status=200)
        return Response({'error': 'Cannot enroll'}, status=400)

    def get(self, request, **kwargs):
        if 'badgeclass_slug' not in kwargs:
            return Response(data='field missing', status=500)
        return super(StudentsEnrolledList, self).get(request, **kwargs)


class StudentsEnrolledDetail(BaseEntityDetailView):
    """
    PUT: update enrollment
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer

    def put(self, request, **kwargs):
        enrollment = request.data['enrollment']
        current_badgeclass = BadgeClass.objects.get(entity_id=request.data['badge_class'])
        if not self.has_object_permissions(request, current_badgeclass):
            return Response(data= 'You do not have permission', status=HTTP_404_NOT_FOUND)
        if enrollment:
            enrollments_for_badgeclass = StudentsEnrolled.objects.filter(badge_class=current_badgeclass)
            enrollment_object = enrollments_for_badgeclass.get(edu_id=enrollment['recipient_identifier'])
            enrollment_object.denied = enrollment['denied']
            enrollment_object.save()
            message = 'Succesfully updated enrollment of {}'.format(enrollment['recipient_name'].encode('utf-8'))
            return Response(data=message, status=HTTP_200_OK)
        return Response(data='No enrollment to deny', status=HTTP_400_BAD_REQUEST)