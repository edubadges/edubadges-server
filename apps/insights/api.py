from datetime import datetime
from datetime import timedelta
from itertools import groupby

from django.conf import settings
from django.db import connection
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
                start_of_year = start_of_year + timedelta(days=(7 + 1) - start_of_year.isoweekday())
            end_of_year = current_date.replace(year=year, month=12, day=31)
            if end_of_year.isoweekday() > 1:
                end_of_year = end_of_year + timedelta(days=(7 + 1) - end_of_year.isoweekday())
        # Superusers may select an institution
        institution_id = request.data.get('institution_id')
        filter_by_institution = True
        if institution_id and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            if institution_id == 'all':
                filter_by_institution = False
            else:
                institution = Institution.objects.get(entity_id=institution_id)
        else:
            institution = request.user.institution
        include_surf = request.data.get('include_surf', True)
        today = datetime.utcnow()
        assertions_query_set = (
            BadgeInstance.objects.values(
                'award_type',
                'badgeclass_id',
                'badgeclass__name',
                'badgeclass__archived',
                'badgeclass__badge_class_type',
                'issuer_id',
                'public',
                'revoked',
                'issuer__name_dutch',
                'issuer__name_english',
                'issuer__faculty_id',
                'issuer__faculty__name_english',
                'issuer__faculty__name_dutch',
                'issuer__faculty__faculty_type',
                'issuer__faculty__institution__institution_type',
            )
            .annotate(year=ExtractYear('created_at'))
            .annotate(month=ExtractMonth('created_at'))
            .annotate(nbr=Count('month'))
            .values(
                'year',
                'month',
                'nbr',
                'award_type',
                'badgeclass_id',
                'badgeclass__name',
                'badgeclass__archived',
                'badgeclass__badge_class_type',
                'issuer_id',
                'public',
                'revoked',
                'issuer__name_dutch',
                'issuer__name_english',
                'issuer__faculty_id',
                'issuer__faculty__name_dutch',
                'issuer__faculty__name_english',
                'issuer__faculty__faculty_type',
                'issuer__faculty__institution__institution_type',
            )
            .exclude(expires_at__lte=today)
            .order_by('year', 'month')
        )
        if not total:
            assertions_query_set = assertions_query_set.filter(created_at__gte=start_of_year).filter(
                created_at__lt=end_of_year
            )
        if filter_by_institution:
            assertions_query_set = assertions_query_set.filter(issuer__faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            assertions_query_set = assertions_query_set.exclude(issuer__faculty__institution=surf_institution)

        direct_awards_query_set = (
            DirectAward.objects.values(
                'status',
                'badgeclass_id',
                'badgeclass__name',
                'badgeclass__archived',
                'badgeclass__issuer__id',
                'badgeclass__badge_class_type',
                'badgeclass__issuer__name_dutch',
                'badgeclass__issuer__name_english',
                'badgeclass__issuer__faculty_id',
                'badgeclass__issuer__faculty__name_english',
                'badgeclass__issuer__faculty__name_dutch',
                'badgeclass__issuer__faculty__faculty_type',
                'badgeclass__issuer__faculty__institution__institution_type',
            )
            .annotate(year=ExtractYear('created_at'))
            .annotate(month=ExtractMonth('created_at'))
            .annotate(nbr=Count('month'))
            .values(
                'month',
                'year',
                'nbr',
                'status',
                'badgeclass_id',
                'badgeclass__name',
                'badgeclass__archived',
                'badgeclass__issuer__id',
                'badgeclass__badge_class_type',
                'badgeclass__issuer__name_dutch',
                'badgeclass__issuer__name_english',
                'badgeclass__issuer__faculty_id',
                'badgeclass__issuer__faculty__name_dutch',
                'badgeclass__issuer__faculty__name_english',
                'badgeclass__issuer__faculty__faculty_type',
                'badgeclass__issuer__faculty__institution__institution_type',
            )
            .order_by('year', 'month')
            .exclude(status='Deleted')
            .exclude(status='Revoked')
            .exclude(status='Scheduled')
        )

        if not total:
            direct_awards_query_set = direct_awards_query_set.filter(created_at__gte=start_of_year).filter(
                created_at__lt=end_of_year
            )
        if filter_by_institution:
            direct_awards_query_set = direct_awards_query_set.filter(
                badgeclass__issuer__faculty__institution=institution
            )
        if not filter_by_institution and not include_surf:
            direct_awards_query_set = direct_awards_query_set.exclude(
                badgeclass__issuer__faculty__institution=surf_institution
            )

        enrollments_query_set = (
            StudentsEnrolled.objects.filter(Q(badge_instance_id__isnull=True) | Q(denied=True))
            .values(
                'denied',
                'badge_class_id',
                'badge_class__name',
                'badge_class__issuer__id',
                'badge_class__issuer__name_dutch',
                'badge_class__issuer__name_english',
                'badge_class__issuer__faculty_id',
                'badge_class__badge_class_type',
                'badge_class__issuer__faculty__name_dutch',
                'badge_class__issuer__faculty__name_english',
                'badge_class__issuer__faculty__faculty_type',
                'badge_class__issuer__faculty__institution__institution_type',
            )
            .annotate(year=ExtractYear('date_created'))
            .annotate(month=ExtractMonth('date_created'))
            .annotate(nbr=Count('month'))
            .values(
                'month',
                'year',
                'nbr',
                'denied',
                'badge_class_id',
                'badge_class__name',
                'badge_class__issuer__id',
                'badge_class__badge_class_type',
                'badge_class__issuer__name_dutch',
                'badge_class__issuer__name_english',
                'badge_class__issuer__faculty_id',
                'badge_class__issuer__faculty__name_dutch',
                'badge_class__issuer__faculty__name_english',
                'badge_class__issuer__faculty__faculty_type',
                'badge_class__issuer__faculty__institution__institution_type',
            )
            .order_by('year', 'month')
        )

        if not total:
            enrollments_query_set = enrollments_query_set.filter(date_created__gte=start_of_year).filter(
                date_created__lt=end_of_year
            )
        if filter_by_institution:
            enrollments_query_set = enrollments_query_set.filter(badge_class__issuer__faculty__institution=institution)
        if not filter_by_institution and not include_surf:
            enrollments_query_set = enrollments_query_set.exclude(
                badge_class__issuer__faculty__institution=surf_institution
            )

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
            'backpack_count': backpack_count,
        }
        return Response(res, status=status.HTTP_200_OK)


class InstitutionAdminsView(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = (
            InstitutionStaff.objects.values(
                'institution__name_english',
                'institution__name_dutch',
                'user__first_name',
                'user__last_name',
                'user__email',
            )
            .filter(
                may_create=True,
                may_update=True,
                may_delete=True,
                may_award=True,
                may_sign=True,
                may_administrate_users=True,
            )
            .all()
        )
        institution_admins = list(query_set)
        return Response(institution_admins, status=status.HTTP_200_OK)


class InstitutionBadgesView(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = (
            BadgeInstance.objects.values(
                'award_type',
                'revoked',
                'badgeclass__name',
                'badgeclass__issuer__faculty__name_english',
                'badgeclass__issuer__faculty__institution__name_english',
            )
            .annotate(count=Count('id'))
            .order_by('count')
            .all()
        )
        institution_badges = list(query_set)
        return Response(institution_badges, status=status.HTTP_200_OK)


class InstitutionMicroCredentials(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        query_set = (
            BadgeInstance.objects.values(
                'badgeclass__issuer__faculty__institution__name_english',
                'badgeclass__issuer__faculty__institution__identifier',
            )
            .annotate(count=Count('id'))
            .filter(badgeclass__badge_class_type='micro_credential')
            .order_by('count')
            .all()
        )
        institution_badges = list(query_set)
        return Response(institution_badges, status=status.HTTP_200_OK)


class CountMicroCredentials(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select ins.identifier, count(u.id) as user_count, (select count(bi.id) from issuer_badgeinstance bi where bi.user_id = u.id ) as assertion_count 
from users u 
 inner join issuer_badgeinstance bi on bi.user_id = u.id
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 inner join issuer_issuer i on i.id = b.issuer_id 
 inner join institution_faculty f on f.id = i.faculty_id 
 inner join institution_institution ins on ins.id = f.institution_id 
 where b.badge_class_type = 'micro_credential' and ins.institution_type is not null
 group by assertion_count, ins.identifier ;            
            """,
                [],
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class MicroCredentialsBadgeOverview(APIView):
    permission_classes = (IsSuperUser,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select b.id, b.name as badgeclass_name, ins.name_english as institution_name, ins.identifier, b.created_at ,
(select original_json from issuer_badgeclassextension where name = 'extensions:EQFExtension' and badgeclass_id = b.id limit 1) as eqf_value,
(select original_json from issuer_badgeclassextension where name = 'extensions:ECTSExtension' and badgeclass_id = b.id limit 1) as ects_value,
 (select original_json from issuer_badgeclassextension where name = 'extensions:StudyLoadExtension' and badgeclass_id = b.id limit 1) as study_load
 from issuer_badgeclass b
 inner join issuer_issuer i on i.id = b.issuer_id
 inner join institution_faculty f on f.id = i.faculty_id
 inner join institution_institution ins on ins.id = f.institution_id
 where b.badge_class_type = 'micro_credential' and ins.institution_type is not null;
             """,
                [],
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class InstitutionBadgesOverview(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        is_super_user = hasattr(request.user, 'is_superuser') and request.user.is_superuser
        institution_id = None if is_super_user else request.user.institution.id

        with connection.cursor() as cursor:
            cursor.execute(
                """
select b.id as badge_class_id, bi.award_type, b.name as badge_name,  b.badge_class_type, bi.public as public_badge,
bi.revoked, i.name_english as issuer_name, f.name_english as issuergroup_name, ins.name_english as institution_name,
ins.institution_type as institution_type, count(bi.id) as backpack_count, 'N/A' as claim_rate, 0 as total_da_count,
(SELECT count(1) FROM directaward_directawardaudittrail trail WHERE trail.action = 'ACCEPT' and trail.badgeclass_id = b.id and trail.user_agent_info like "Java-http-client%%") as awarded_via_sis,
(SELECT count(1) FROM directaward_directawardaudittrail trail WHERE trail.action = 'ACCEPT' and trail.badgeclass_id = b.id and not trail.user_agent_info like "Java-http-client%%") as awarded_via_ui
from issuer_badgeinstance bi
inner join issuer_badgeclass b on b.id = bi.badgeclass_id
inner join issuer_issuer i on i.id = b.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where (bi.expires_at >= CURDATE() or bi.expires_at is NULL) and ((ins.id = %(ins_id)s and not %(ins_id)s is null) or %(ins_id)s is null)
group by b.id, bi.award_type, bi.public, bi.revoked;
            """,
                {'ins_id': institution_id},
            )
            badge_overview = dict_fetch_all(cursor)

            cursor.execute(
                """
select count(id) as da_count, badgeclass_id as badgeclass_id
from directaward_directaward da where status <> 'Deleted' and status <> 'Revoked' and status <> 'Scheduled' group by badgeclass_id;
                        """,
                [],
            )
            da_overview = dict_fetch_all(cursor)

            # Now group by badgeclass_id and create final reporting dict
            def key_func(k):
                return str(k['badge_class_id'])

            def claim_rate(total_direct_award_count, direct_award_accepted):
                if total_direct_award_count == 0:
                    return 'N/A'
                return round((direct_award_accepted / total_direct_award_count) * 100)

            # Known caveat is to forget sorting before groupby
            sorted_assertions = sorted(badge_overview, key=key_func)
            grouped_assertions = groupby(sorted_assertions, key_func)
            results = []
            for key, val in grouped_assertions:
                values = list(val)
                badge_instance = values[0]
                direct_awards_accepted = sum(
                    [b['backpack_count'] for b in values if b['award_type'] == 'direct_award' and not b['revoked']]
                )
                direct_awards_assertions_revoked = sum(
                    [b['backpack_count'] for b in values if b['award_type'] == 'direct_award' and b['revoked']]
                )
                direct_awards_rejected_or_unaccepted = sum(
                    [da['da_count'] for da in da_overview if str(da['badgeclass_id']) == str(key)]
                )
                total_da_count = (
                    direct_awards_accepted + direct_awards_rejected_or_unaccepted + direct_awards_assertions_revoked
                )
                results.append(
                    {
                        'Institution name': badge_instance['institution_name'],
                        'Sector': badge_instance['institution_type'],
                        'Issuergroup name': badge_instance['issuergroup_name'],
                        'Issuer name': badge_instance['issuer_name'],
                        'BadgecClass name': badge_instance['badge_name'],
                        'Type': badge_instance['badge_class_type'],
                        'Total edubadges in backpack': sum([b['backpack_count'] for b in values if not b['revoked']]),
                        'DA claimed': direct_awards_accepted,
                        'Requested accepted': sum(
                            [b['backpack_count'] for b in values if b['award_type'] == 'requested' and not b['revoked']]
                        ),
                        'DA revoked': direct_awards_assertions_revoked,
                        'Requested revoked': sum(
                            [b['backpack_count'] for b in values if b['award_type'] == 'requested' and b['revoked']]
                        ),
                        'Public': sum([b['backpack_count'] for b in values if b['public_badge']]),
                        'Claim-rate': claim_rate(
                            (total_da_count - direct_awards_assertions_revoked), direct_awards_accepted
                        ),
                        'Total DA send': total_da_count,
                        'Awarded via UI': badge_instance['awarded_via_ui'],
                        'Awarded via SIS': badge_instance['awarded_via_sis'],
                    }
                )

            sorted_results = sorted(results, key=lambda a: (a['Institution name'], a['BadgecClass name']))
            return Response(sorted_results, status=status.HTTP_200_OK)


class IssuerMembers(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        is_super_user = hasattr(request.user, 'is_superuser') and request.user.is_superuser
        institution_part = '' if is_super_user else f'ins.id = {request.user.institution.id} and '

        with connection.cursor() as cursor:
            cursor.execute(
                f"""
select i.id, u.email, u.first_name, u.last_name, i.name_english as issuer_name_en, i.name_dutch  as issuer_name_nl, 
si.may_update as issuer_staff
from users u
inner join staff_issuerstaff si on u.id = si.user_id
inner join issuer_issuer i on i.id = si.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where {institution_part} si.may_update is not null and i.id is not null order by i.id;
                        """,
                [],
            )
            issuer_overview = dict_fetch_all(cursor)

            def determine_role(row):
                return 'Issuer Admin' if row['issuer_staff'] else 'Issuer Awarder'

            results = []

            for row in issuer_overview:
                results.append(
                    {
                        'issuer_name': row['issuer_name_en'] if row['issuer_name_en'] else row['issuer_name_nl'],
                        'email': row['email'],
                        'name': f'{row["first_name"]} {row["last_name"]}',
                        'role': determine_role(row),
                    }
                )
            sorted_results = sorted(results, key=lambda a: (a['issuer_name'],))
            return Response(sorted_results, status=status.HTTP_200_OK)
