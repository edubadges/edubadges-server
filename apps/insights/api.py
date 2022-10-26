from datetime import datetime
from datetime import timedelta

from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import BadgeUser, StudentAffiliation
from directaward.models import DirectAward
from institution.models import Faculty, Institution
from issuer.models import BadgeInstance, Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite.permissions import TeachPermission


class InsightsView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        lang = request.data.get('lang', 'en')

        current_date = timezone.now().date()
        year = request.data.get('year', current_date.year)
        total = isinstance(year, str)
        if not total:
            start_of_year = current_date.replace(year=year, month=1, day=1)
            if start_of_year.isoweekday() > 1:
                start_of_year = (start_of_year + timedelta(days=(7 + 1) - start_of_year.isoweekday()))
            end_of_year = current_date.replace(year=year, month=12, day=31)
            if end_of_year.isoweekday() > 1:
                end_of_year = (end_of_year + timedelta(days=(7 + 1) - end_of_year.isoweekday()))
        # Super users may select an institution
        institution_id = request.data.get("institution_id")
        filter_by_institution = True
        if institution_id and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            if institution_id == "all":
                filter_by_institution = False
            else:
                institution = Institution.objects.get(entity_id=institution_id)
        else:
            institution = request.user.institution

        student_affiliation_query = StudentAffiliation.objects.values_list('user_id', flat=True).all()
        today = datetime.today()
        assertions_query_set = BadgeInstance.objects \
            .values('award_type', 'badgeclass_id', 'badgeclass__name', 'issuer_id', "public", "revoked",
                    "issuer__name_dutch", "issuer__name_english", 'issuer__faculty_id',
                    "issuer__faculty__name_english", "issuer__faculty__name_dutch") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('year', 'month', 'nbr', 'award_type', 'badgeclass_id', 'badgeclass__name', 'issuer_id',
                    "public", "revoked", "issuer__name_dutch", "issuer__name_english", 'issuer__faculty_id',
                    "issuer__faculty__name_dutch", "issuer__faculty__name_english") \
            .filter(user__id__in=student_affiliation_query) \
            .exclude(expires_at__lte=today) \
            .exclude(badgeclass__name=settings.EDUID_BADGE_CLASS_NAME) \
            .order_by('year', 'month')
        if not total:
            assertions_query_set = assertions_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)
        if filter_by_institution:
            assertions_query_set = assertions_query_set \
                .filter(issuer__faculty__institution=institution)

        direct_awards_query_set = DirectAward.objects \
            .values('status', 'badgeclass_id', 'badgeclass__name', 'badgeclass__issuer__id',
                    "badgeclass__issuer__name_dutch", "badgeclass__issuer__name_english",
                    'badgeclass__issuer__faculty_id',
                    "badgeclass__issuer__faculty__name_english", "badgeclass__issuer__faculty__name_dutch") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'status', 'badgeclass_id', 'badgeclass__name',
                    'badgeclass__issuer__id',
                    "badgeclass__issuer__name_dutch", "badgeclass__issuer__name_english",
                    'badgeclass__issuer__faculty_id',
                    "badgeclass__issuer__faculty__name_dutch", "badgeclass__issuer__faculty__name_english") \
            .order_by('year', 'month')

        if not total:
            direct_awards_query_set = direct_awards_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)
        if filter_by_institution:
            direct_awards_query_set = direct_awards_query_set \
                .filter(badgeclass__issuer__faculty__institution=institution)

        enrollments_query_set = StudentsEnrolled.objects \
            .filter(Q(badge_instance_id__isnull=True) | Q(denied=True)) \
            .values('denied', 'badge_class_id', 'badge_class__name', 'badge_class__issuer__id',
                    "badge_class__issuer__name_dutch", "badge_class__issuer__name_english",
                    'badge_class__issuer__faculty_id',
                    "badge_class__issuer__faculty__name_dutch", "badge_class__issuer__faculty__name_english") \
            .annotate(year=ExtractYear('date_created')) \
            .annotate(month=ExtractMonth('date_created')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'denied', 'badge_class_id', 'badge_class__name',
                    'badge_class__issuer__id',
                    "badge_class__issuer__name_dutch", "badge_class__issuer__name_english",
                    'badge_class__issuer__faculty_id',
                    "badge_class__issuer__faculty__name_dutch", "badge_class__issuer__faculty__name_english") \
            .order_by('year', 'month')

        if not total:
            enrollments_query_set = enrollments_query_set \
                .filter(date_created__gte=start_of_year) \
                .filter(date_created__lt=end_of_year)
        if filter_by_institution:
            enrollments_query_set = enrollments_query_set \
                .filter(badge_class__issuer__faculty__institution=institution)

        assertions = list(assertions_query_set.all())
        direct_awards = list(direct_awards_query_set.all())
        enrollments = list(enrollments_query_set.all())

        badge_user_query = BadgeUser.objects.filter(is_teacher=True)
        if filter_by_institution:
            badge_user_query = badge_user_query.filter(institution=institution)
        users_count = badge_user_query.count()

        faculty_query = Faculty.objects
        if filter_by_institution:
            faculty_query = faculty_query.filter(institution=institution)
        faculties_count = faculty_query.count()

        issuer_query = Issuer.objects
        if filter_by_institution:
            issuer_query = issuer_query.filter(faculty__institution=institution)
        issuer_count = issuer_query.count()

        badge_class_query = BadgeClass.objects
        if filter_by_institution:
            badge_class_query = badge_class_query.filter(issuer__faculty__institution=institution)
        badge_class_count = badge_class_query.count()

        backpack_query = StudentAffiliation.objects
        if filter_by_institution:
            backpack_query = backpack_query.filter(schac_home=institution.identifier)
        backpack_count = backpack_query.count()

        res = {
            'assertions': assertions,
            'direct_awards': direct_awards,
            'enrollments': enrollments,
            'users_count': users_count,
            'faculties_count': faculties_count,
            'issuers_count': issuer_count,
            'badge_class_count': badge_class_count,
            'backpack_count': backpack_count
        }
        return Response(res, status=status.HTTP_200_OK)
