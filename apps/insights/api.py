from datetime import datetime
from datetime import timedelta
from django.db import connection
from itertools import groupby
from django.conf import settings
from django.db.models import Count
from django.db.models import Q
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import BadgeUser, StudentAffiliation
from badgrsocialauth.permissions import IsSuperUser
from directaward.models import DirectAward
from institution.models import Faculty, Institution
from issuer.models import BadgeInstance, Issuer, BadgeClass
from lti_edu.models import StudentsEnrolled
from mainsite.permissions import TeachPermission
from staff.models import InstitutionStaff


def dict_fetch_all(cursor):
    desc = cursor.description
    rows = cursor.fetchall()
    res = [dict(zip([col[0] for col in desc], row)) for row in rows]
    return res


class InsightsView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        surf_institution = BadgeClass.objects.get(name=settings.EDUID_BADGE_CLASS_NAME).issuer.faculty.institution
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
        # Superusers may select an institution
        institution_id = request.data.get("institution_id")
        filter_by_institution = True
        if institution_id and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            if institution_id == "all":
                filter_by_institution = False
            else:
                institution = Institution.objects.get(entity_id=institution_id)
        else:
            institution = request.user.institution
        include_surf = request.data.get("include_surf", True)
        # For now we don't use the student_affiliation_query
        # student_affiliation_query = StudentAffiliation.objects.values_list('user_id', flat=True).all()
        # .filter(user__id__in=student_affiliation_query) \
        today = datetime.utcnow()
        assertions_query_set = BadgeInstance.objects \
            .values('award_type', 'badgeclass_id', 'badgeclass__name', 'badgeclass__is_micro_credentials',
                    'issuer_id', "public", "revoked",
                    "issuer__name_dutch", "issuer__name_english", 'issuer__faculty_id',
                    "issuer__faculty__name_english", "issuer__faculty__name_dutch") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('year', 'month', 'nbr', 'award_type', 'badgeclass_id', 'badgeclass__name',
                    'badgeclass__is_micro_credentials', 'issuer_id',
                    "public", "revoked", "issuer__name_dutch", "issuer__name_english", 'issuer__faculty_id',
                    "issuer__faculty__name_dutch", "issuer__faculty__name_english") \
            .exclude(expires_at__lte=today) \
            .order_by('year', 'month')
        if not total:
            assertions_query_set = assertions_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)
        if filter_by_institution:
            assertions_query_set = assertions_query_set \
                .filter(issuer__faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            assertions_query_set = assertions_query_set \
                .exclude(issuer__faculty__institution=surf_institution)

        direct_awards_query_set = DirectAward.objects \
            .values('status', 'badgeclass_id', 'badgeclass__name', 'badgeclass__issuer__id',
                    'badgeclass__is_micro_credentials',
                    "badgeclass__issuer__name_dutch", "badgeclass__issuer__name_english",
                    'badgeclass__issuer__faculty_id',
                    "badgeclass__issuer__faculty__name_english", "badgeclass__issuer__faculty__name_dutch") \
            .annotate(year=ExtractYear('created_at')) \
            .annotate(month=ExtractMonth('created_at')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'status', 'badgeclass_id', 'badgeclass__name',
                    'badgeclass__issuer__id', 'badgeclass__is_micro_credentials',
                    "badgeclass__issuer__name_dutch", "badgeclass__issuer__name_english",
                    'badgeclass__issuer__faculty_id',
                    "badgeclass__issuer__faculty__name_dutch", "badgeclass__issuer__faculty__name_english") \
            .order_by('year', 'month') \
            .exclude(status='Deleted').exclude(status='Revoked')

        if not total:
            direct_awards_query_set = direct_awards_query_set \
                .filter(created_at__gte=start_of_year) \
                .filter(created_at__lt=end_of_year)
        if filter_by_institution:
            direct_awards_query_set = direct_awards_query_set \
                .filter(badgeclass__issuer__faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            direct_awards_query_set = direct_awards_query_set \
                .exclude(badgeclass__issuer__faculty__institution=surf_institution)

        enrollments_query_set = StudentsEnrolled.objects \
            .filter(Q(badge_instance_id__isnull=True) | Q(denied=True)) \
            .values('denied', 'badge_class_id', 'badge_class__name', 'badge_class__issuer__id',
                    "badge_class__issuer__name_dutch", "badge_class__issuer__name_english",
                    'badge_class__issuer__faculty_id', 'badge_class__is_micro_credentials',
                    "badge_class__issuer__faculty__name_dutch", "badge_class__issuer__faculty__name_english") \
            .annotate(year=ExtractYear('date_created')) \
            .annotate(month=ExtractMonth('date_created')) \
            .annotate(nbr=Count('month')) \
            .values('month', 'year', 'nbr', 'denied', 'badge_class_id', 'badge_class__name',
                    'badge_class__issuer__id', 'badge_class__is_micro_credentials',
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
        if not filter_by_institution and not include_surf:
            enrollments_query_set = enrollments_query_set \
                .exclude(badge_class__issuer__faculty__institution=surf_institution)

        assertions = list(assertions_query_set.all())
        direct_awards = list(direct_awards_query_set.all())
        enrollments = list(enrollments_query_set.all())

        badge_user_query = BadgeUser.objects.filter(is_teacher=True)
        if filter_by_institution:
            badge_user_query = badge_user_query.filter(institution=institution)
        if not filter_by_institution and not include_surf:
            badge_user_query = badge_user_query.exclude(institution=surf_institution)
        users_count = badge_user_query.count()

        faculty_query = Faculty.objects
        if filter_by_institution:
            faculty_query = faculty_query.filter(institution=institution)
        if not filter_by_institution and not include_surf:
            faculty_query = faculty_query.exclude(institution=surf_institution)
        faculties_count = faculty_query.count()

        issuer_query = Issuer.objects
        if filter_by_institution:
            issuer_query = issuer_query.filter(faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            issuer_query = issuer_query.exclude(faculty__institution=surf_institution)
        issuer_count = issuer_query.count()

        badge_class_query = BadgeClass.objects
        if filter_by_institution:
            badge_class_query = badge_class_query.filter(issuer__faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            badge_class_query = badge_class_query.exclude(issuer__faculty__institution=surf_institution)
        badge_class_count = badge_class_query.count()

        backpack_query = StudentAffiliation.objects
        if filter_by_institution:
            backpack_query = backpack_query.filter(schac_home=institution.identifier)
        if not filter_by_institution and not include_surf:
            backpack_query = backpack_query.exclude(schac_home__iexact=surf_institution.identifier)
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


class InstitutionAdminsView(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = InstitutionStaff.objects \
            .values('institution__name_english', 'institution__name_dutch', 'user__first_name',
                    'user__last_name', 'user__email') \
            .filter(may_create=True, may_update=True, may_delete=True, may_award=True, may_sign=True,
                    may_administrate_users=True) \
            .all()
        institution_admins = list(query_set)
        return Response(institution_admins, status=status.HTTP_200_OK)


class InstitutionBadgesView(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = BadgeInstance.objects \
            .values('award_type', 'revoked', 'badgeclass__name', 'badgeclass__issuer__faculty__name_english',
                    'badgeclass__issuer__faculty__institution__name_english') \
            .annotate(count=Count('id')) \
            .order_by('count') \
            .all()
        institution_badges = list(query_set)
        return Response(institution_badges, status=status.HTTP_200_OK)


class InstitutionMicroCredentials(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = BadgeInstance.objects \
            .values('badgeclass__issuer__faculty__institution__name_english',
                    'badgeclass__issuer__faculty__institution__identifier') \
            .annotate(count=Count('id')) \
            .filter(badgeclass__is_micro_credentials=True) \
            .order_by('count') \
            .all()
        institution_badges = list(query_set)
        return Response(institution_badges, status=status.HTTP_200_OK)


class CountMicroCredentials(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
select ins.identifier, count(u.id) as user_count, (select count(bi.id) from issuer_badgeinstance bi where bi.user_id = u.id ) as assertion_count 
from users u 
 inner join issuer_badgeinstance bi on bi.user_id = u.id
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 inner join issuer_issuer i on i.id = b.issuer_id 
 inner join institution_faculty f on f.id = i.faculty_id 
 inner join institution_institution ins on ins.id = f.institution_id 
 where b.is_micro_credentials = 1 and ins.institution_type is not null
 group by assertion_count, ins.identifier ;            
            """, [])
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class MicroCredentialsBadgeOverview(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
select b.id, b.name as badgeclass_name, ins.name_english as institution_name, ins.identifier, b.created_at ,
(select original_json from issuer_badgeclassextension where name = 'extensions:EQFExtension' and badgeclass_id = b.id limit 1) as eqf_value,
(select original_json from issuer_badgeclassextension where name = 'extensions:ECTSExtension' and badgeclass_id = b.id limit 1) as ects_value,
 (select original_json from issuer_badgeclassextension where name = 'extensions:StudyLoadExtension' and badgeclass_id = b.id limit 1) as study_load
 from issuer_badgeclass b
 inner join issuer_issuer i on i.id = b.issuer_id
 inner join institution_faculty f on f.id = i.faculty_id
 inner join institution_institution ins on ins.id = f.institution_id
 where b.is_micro_credentials = 1 and ins.institution_type is not null;
             """, [])
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class InstitutionBadgesOverview(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
select b.id as badge_class_id, bi.award_type, b.name as badge_name,  b.is_micro_credentials, bi.public as public_badge,
bi.revoked, ins.name_english as institution_name, count(bi.id) as backpack_count, 'N/A' as claim_rate, 0 as total_da_count
from issuer_badgeinstance bi
inner join issuer_badgeclass b on b.id = bi.badgeclass_id
inner join issuer_issuer i on i.id = b.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where bi.expires_at >= CURDATE() or bi.expires_at is NULL
group by b.id, bi.award_type, bi.public, bi.revoked;
            """, [])
            badge_overview = dict_fetch_all(cursor)
            cursor.execute("""
select count(id) as da_count, badgeclass_id as badgeclass_id from directaward_directaward 
where status <>  'Deleted' and status <> 'Revoked' group by badgeclass_id;
                        """, [])
            da_overview = dict_fetch_all(cursor)

            # Now add the claim-rate which is:
            # (directAwardNonRevokedBadges / (Total Direct awards - directAwardRevokedBadges))
            def find_direct_awards(badge, badge_class_identifer):
                return badge['award_type'] == 'direct_award' and badge['badge_class_id'] == badge_class_identifer

            for da in da_overview:
                da_badges = [b for b in badge_overview if find_direct_awards(b, da['badgeclass_id'])]
                da_revoked = sum([b['backpack_count'] for b in da_badges if b['revoked']])
                da_not_revoked = sum([b['backpack_count'] for b in da_badges if not b['revoked']])
                total_da_count = da['da_count'] + da_not_revoked + da_revoked
                try:
                    claim_rate = round((da_not_revoked / (total_da_count - da_revoked)) * 100)
                except ZeroDivisionError:
                    claim_rate = 0
                for b in da_badges:
                    b['claim_rate'] = f"{claim_rate}%"
                    b['total_da_count'] = total_da_count

            # Now group by badgeclass_id and create final reporting dict
            def key_func(k):
                return str(k['badge_class_id'])

            # Known caveat is to forget sorting before groupby
            sorted_assertions = sorted(badge_overview, key=key_func)
            grouped_assertions = groupby(sorted_assertions, key_func)
            results = []
            for key, val in grouped_assertions:
                values = list(val)
                badge_instance = values[0]
                claim_rates = [v['claim_rate'] for v in values if v['claim_rate'] != 'N/A']
                claim_rate = claim_rates[0] if claim_rates else 'N/A'
                da_counts = [v['total_da_count'] for v in values if v['total_da_count'] != 0]
                total_da_count = da_counts[0] if da_counts else 0
                results.append({
                    'Institution name': badge_instance['institution_name'],
                    'BadgecClass name': badge_instance['badge_name'],
                    'Type': 'Microcredential' if badge_instance['is_micro_credentials'] else 'Other',
                    'Total edubadges in backpack': sum([b['backpack_count'] for b in values if not b['revoked']]),
                    'DA claimed': sum(
                        [b['backpack_count'] for b in values if
                         b['award_type'] == 'direct_award' and not b['revoked']]),
                    'Requested accepted': sum(
                        [b['backpack_count'] for b in values if b['award_type'] == 'requested' and not b['revoked']]),
                    'DA revoked': sum(
                        [b['backpack_count'] for b in values if b['award_type'] == 'direct_award' and b['revoked']]),
                    'Requested revoked': sum(
                        [b['backpack_count'] for b in values if b['award_type'] == 'requested' and b['revoked']]),
                    'Public': sum([b['backpack_count'] for b in values if b['public_badge']]),
                    'Claim-rate': claim_rate,
                    'Total DA send': total_da_count
                })

            sorted_results = sorted(results, key=lambda a: (a['Institution name'], a['BadgecClass name']))
            return Response(sorted_results, status=status.HTTP_200_OK)
