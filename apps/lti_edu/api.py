from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import BadgeClass
from lti_edu.models import StudentsEnrolled, BadgeClassLtiContext, UserCurrentContextId
from lti_edu.serializers import StudentsEnrolledSerializer, StudentsEnrolledSerializerWithRelations, \
    BadgeClassLtiContextSerializer, BadgeClassLtiContextStudentSerializer
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST


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


class StudentEnrollmentList(BaseEntityListView):
    """
    GET a list of enrollments for a student
    DELETE to delete enrollment
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializerWithRelations

    def get_objects(self, request, **kwargs):
        return StudentsEnrolled.objects.filter(user=request.user)

    def get(self, request, **kwargs):
        return super(StudentEnrollmentList, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        enrollment = StudentsEnrolled.objects.get(id=request.data['enrollmentID'])
        if enrollment.date_awarded:
            return Response(data='Awarded enrollments cannot be withdrawn', status=403)
        if request.user == enrollment.user:
            enrollment.delete()
            return Response(data='Enrollment successfully withdrawn', status=200)
        else:
            return Response(data='Users can only withdraw their own enrollments', status=403)


class StudentsEnrolledList(BaseEntityListView):
    """
    GET: get  list of not-awarded enrollments for a badgeclass
    POST: to enroll student
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializer

    def get_objects(self, request, **kwargs):
        badge_class = get_object_or_404(BadgeClass, entity_id=kwargs['badgeclass_slug'])
        return StudentsEnrolled.objects.filter(badge_class_id=badge_class.pk,
                                               date_awarded=None)

    def post(self, request, **kwargs):
        for field in ['badgeclass_slug']:
            if field not in request.data:
                return Response(data='field missing', status=401)
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])
        if request.user.may_enroll(badge_class):
            # consent given when enrolling
            enrollment = StudentsEnrolled.objects.create(badge_class_id=badge_class.pk,
                                                         user=request.user,
                                                         date_consent_given=timezone.now())
            message = EmailMessageMaker.create_student_badge_request_email(badge_class)
            request.user.email_user(subject='You have successfully requested a badge', message=message)
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
            enrollment_object = StudentsEnrolled.objects.get(entity_id=enrollment['enrollment_slug'])
            enrollment_object.denied = enrollment['denied']
            enrollment_object.save()
            message = 'Succesfully updated enrollment of {}'.format(enrollment['recipient_name'].encode('utf-8'))
            return Response(data=message, status=HTTP_200_OK)
        return Response(data='No enrollment to deny', status=HTTP_400_BAD_REQUEST)


class BadgeClassLtiContextListView(BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    model = BadgeClassLtiContext
    serializer_class = BadgeClassLtiContextSerializer

    def get_objects(self, request, **kwargs):

        if 'lti_context_id' in kwargs:
            lti_context_id = kwargs['lti_context_id']
            badgeclasses_per_context_id = BadgeClassLtiContext.objects.filter(context_id=lti_context_id).all()
            return badgeclasses_per_context_id
        return []


class BadgeClassLtiContextStudentListView(BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    model = BadgeClassLtiContext
    serializer_class = BadgeClassLtiContextStudentSerializer

    def get_objects(self, request, **kwargs):

        if 'lti_context_id' in kwargs:
            lti_context_id = kwargs['lti_context_id']
            badgeclasses_per_context_id = BadgeClassLtiContext.objects.filter(context_id=lti_context_id).all()
            return badgeclasses_per_context_id
        return []


class BadgeClassLtiContextDetailView(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    model = BadgeClassLtiContext
    serializer_class = BadgeClassLtiContextSerializer

    def post(self, request, **kwargs):

        context_id = request.data['contextId']
        badge_class = BadgeClass.objects.get(entity_id=request.data['badgeClassEntityId'])
        BadgeClassLtiContext.objects.get_or_create(context_id=context_id, badge_class=badge_class)
        message = 'Succesfully added badgeclass'
        return Response(data=message, status=HTTP_200_OK)

    def delete(self, request, **kwargs):
        context_id = request.data['contextId']
        badge_class = BadgeClass.objects.get(entity_id=request.data['badgeClassEntityId'])
        BadgeClassLtiContext.objects.get(context_id=context_id, badge_class=badge_class).delete()
        message = 'Succesfully deleted badgeclass'
        return Response(data=message, status=HTTP_200_OK)


class CurrentContextView(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    def get(self, request,**kwargs):
        response = {'loggedin': True,
                    'lticontext': None}
        if not request.user.is_authenticated:
            response['loggedin'] = False
        else:
            try:
                user_current_context_id = UserCurrentContextId.objects.get(badge_user=request.user)
                response['lticontext'] = user_current_context_id.context_id
            except Exception as e:
                pass



        return JsonResponse(response)
