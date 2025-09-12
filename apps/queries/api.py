from django.db import connection
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from directaward.models import DirectAward
from mainsite.permissions import TeachPermission, AuthenticatedWithVerifiedEmail


from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)

permissions_query = """
(
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_award = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_award = 1))
    or
    (exists (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = %(u_id)s and issst.may_award = 1))
    or
    (exists (select 1 from staff_badgeclassstaff bcst where bcst.badgeclass_id = bc.id and bcst.user_id = %(u_id)s and bcst.may_award = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s and us.is_superuser = 1))
)
"""


def dict_fetch_all(cursor):
    desc = cursor.description
    rows = cursor.fetchall()
    res = [dict(zip([col[0] for col in desc], row)) for row in rows]
    return res


class DirectAwards(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get direct awards for the current user's institution. Filter by status parameter: "
        'unclaimed (unaccepted/scheduled) or deleted awards.',
        parameters=[
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by status: "unclaimed" (default) or "deleted"',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='List of direct awards with badge class and institutional hierarchy information',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Two direct awards',
                        description='Returns two direct award records',
                        response_only=True,
                        value=[
                            {
                                'created_at': '2025-05-15T10:30:00.000000',
                                'resend_at': None,
                                'delete_at': '2025-08-15T10:30:00.000000',
                                'recipientEmail': 'student@example.nl',
                                'eppn': 'student@university-example.org',
                                'entityId': 'a1b2c3d4E5f6G7h8I9j0K1',
                                'expiration_date': None,
                                'name': 'Research Methods',
                                'bc_entity_id': 'XyZ123AbC456DeF789GhI012',
                                'i_name_english': 'Department of Social Sciences',
                                'i_name_dutch': 'Faculteit Sociale Wetenschappen',
                                'i_entity_id': 'qRs456TuV789WxY012ZaB345',
                                'f_name_english': 'Faculty of Social Sciences',
                                'f_name_dutch': 'Faculteit Sociale Wetenschappen',
                                'f_entity_id': 'cDe678FgH901IjK234LmN567',
                            },
                            {
                                'created_at': '2025-05-20T14:45:00.000000',
                                'resend_at': '2025-06-01T00:00:00.000000',
                                'delete_at': '2025-08-20T14:45:00.000000',
                                'recipientEmail': 'learner@example.nl',
                                'eppn': 'learner@university-example.org',
                                'entityId': 'oP9q8R7s6T5u4V3w2X1y0Z',
                                'expiration_date': '2026-05-20T00:00:00.000000',
                                'name': 'Academic Writing Skills',
                                'bc_entity_id': 'mNo890PqR123StU456VwX789',
                                'i_name_english': 'University College',
                                'i_name_dutch': 'University College',
                                'i_entity_id': 'yZa234BcD567EfG890HiJ123',
                                'f_name_english': 'Liberal Arts and Sciences',
                                'f_name_dutch': 'Liberal Arts and Sciences',
                                'f_entity_id': 'kLm456NoP789QrS012TuV345',
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access direct awards.'
            ),
        },
    )
    def get(self, request, **kwargs):
        unclaimed = request.GET.get('status', 'unclaimed') == 'unclaimed'
        status_param = (
            [DirectAward.STATUS_UNACCEPTED, DirectAward.STATUS_SCHEDULED] if unclaimed else [DirectAward.STATUS_DELETED]
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
select da.created_at, da.resend_at, da.delete_at, da.recipient_email as recipientEmail, da.eppn, da.entity_id as entityId,
        da.expiration_date,
        bc.name, bc.entity_id as bc_entity_id,
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id
from  directaward_directaward da
inner join issuer_badgeclass bc on bc.id = da.badgeclass_id
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s and da.status in %(status)s and {permissions_query} ;
""",
                {'ins_id': request.user.institution.id, 'u_id': request.user.id, 'status': status_param},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class BadgeClasses(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get all badge classes for the current user's institution with metadata including "
        'assertions counts, enrollment statistics, tags, and staff permissions.',
        responses={
            200: OpenApiResponse(
                description='List of badge classes with full institutional hierarchy and statistics',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Badge classes with statistics',
                        description='Returns badge classes with counts and permissions',
                        response_only=True,
                        value=[
                            {
                                'createdAt': '2025-03-10T09:15:00.000000',
                                'name': 'Data Science Fundamentals',
                                'image': 'uploads/badges/data_science.png',
                                'archived': 0,
                                'entityId': 'Abc123Def456Ghi789Jkl012',
                                'isPrivate': 0,
                                'isMicroCredentials': 1,
                                'typeBadgeClass': 'regular',
                                'i_name_english': 'Computer Science Department',
                                'i_name_dutch': 'Informatica Afdeling',
                                'i_entity_id': 'Mno345Pqr678Stu901Vwx234',
                                'i_image_dutch': 'uploads/issuers/cs_dept.png',
                                'i_image_english': 'uploads/issuers/cs_dept.png',
                                'f_name_english': 'Faculty of Science',
                                'f_name_dutch': 'Faculteit der Exacte Wetenschappen',
                                'f_entity_id': 'Yza567Bcd890Efg123Hij456',
                                'onBehalfOf': 0,
                                'onBehalfOfDisplayName': None,
                                'f_image_dutch': 'uploads/faculty/science.png',
                                'f_image_english': 'uploads/faculty/science.png',
                                'ins_entity_id': 'Klm789Nop012Qrs345Tuv678',
                                'ins_name_english': 'Technical University Example',
                                'ins_name_dutch': 'Technische Universiteit Voorbeeld',
                                'ins_image_dutch': 'uploads/institution/tu_logo.png',
                                'ins_image_english': 'uploads/institution/tu_logo.png',
                                'tags': 'data,science,programming',
                                'selfRequestedAssertionsCount': 12,
                                'directAwardedAssertionsCount': 8,
                                'pendingEnrollmentCount': 3,
                                'ins_staff': None,
                                'fac_staff': 1,
                                'iss_staff': None,
                                'bc_staff': None,
                            },
                            {
                                'createdAt': '2025-04-05T13:20:00.000000',
                                'name': 'Sustainable Development',
                                'image': 'uploads/badges/sustainability.png',
                                'archived': 0,
                                'entityId': 'Wxy901Zab234Cde567Fgh890',
                                'isPrivate': 0,
                                'isMicroCredentials': 0,
                                'typeBadgeClass': 'regular',
                                'i_name_english': 'Environmental Studies',
                                'i_name_dutch': 'Milieukunde',
                                'i_entity_id': 'Ijk123Lmn456Opq789Rst012',
                                'i_image_dutch': '',
                                'i_image_english': 'uploads/issuers/environment.png',
                                'f_name_english': 'Faculty of Social Sciences',
                                'f_name_dutch': 'Faculteit der Sociale Wetenschappen',
                                'f_entity_id': 'Uvw345Xyz678Abc901Def234',
                                'onBehalfOf': 1,
                                'onBehalfOfDisplayName': 'Green Initiative Network',
                                'f_image_dutch': '',
                                'f_image_english': '',
                                'ins_entity_id': 'Ghi567Jkl890Mno123Pqr456',
                                'ins_name_english': 'University of Applied Sciences',
                                'ins_name_dutch': 'Hogeschool',
                                'ins_image_dutch': 'uploads/institution/uas_logo.png',
                                'ins_image_english': 'uploads/institution/uas_logo.png',
                                'tags': 'sustainability,environment',
                                'selfRequestedAssertionsCount': 5,
                                'directAwardedAssertionsCount': 15,
                                'pendingEnrollmentCount': 0,
                                'ins_staff': 1,
                                'fac_staff': None,
                                'iss_staff': None,
                                'bc_staff': None,
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access badge classes.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select bc.created_at as createdAt, bc.name, bc.image, bc.archived, bc.entity_id as entityId,
        bc.is_private as isPrivate, bc.is_micro_credentials as isMicroCredentials,
        bc.badge_class_type as typeBadgeClass,
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id,
        i.image_dutch as i_image_dutch, i.image_english as i_image_english, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        f.on_behalf_of as onBehalfOf, f.on_behalf_of_display_name as onBehalfOfDisplayName, 
        f.image_dutch as f_image_dutch, f.image_english as f_image_english,
        ins.entity_id as ins_entity_id, ins.name_english as ins_name_english, ins.name_dutch as ins_name_dutch,
        ins.image_dutch as ins_image_dutch, ins.image_english as ins_image_english,
        (SELECT STRING_AGG(DISTINCT isbt.name, ',') FROM institution_badgeclasstag isbt
        INNER JOIN issuer_badgeclass_tags ibt ON ibt.badgeclasstag_id = isbt.id
        WHERE ibt.badgeclass_id = bc.id) AS tags,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'requested') as selfRequestedAssertionsCount,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'direct_award') as directAwardedAssertionsCount,
        (select count(id) from lti_edu_studentsenrolled WHERE badge_class_id = bc.id AND badge_instance_id is null AND denied = 0) as pendingEnrollmentCount,
        (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_award = 1) as ins_staff,
        (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_award = 1) as fac_staff,
        (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = %(u_id)s and issst.may_award = 1) as iss_staff,
        (select 1 from staff_badgeclassstaff bcst where bcst.badgeclass_id = bc.id and bcst.user_id = %(u_id)s and bcst.may_award = 1) as bc_staff
from  issuer_badgeclass bc
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s ;
            """,
                {'ins_id': request.user.institution.id, 'u_id': request.user.id},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class CurrentInstitution(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    @extend_schema(
        methods=['GET'],
        description="Get the current user's institution details including administrators and user permissions. "
        'Returns empty objects if the user has no associated institution.',
        responses={
            200: OpenApiResponse(
                description='Current institution data with administrators list and user permissions',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Institution with permissions',
                        description='Returns institution details, admins, and user permissions',
                        response_only=True,
                        value={
                            'current_institution': {
                                'id': 42,
                                'name_english': 'SURF',
                                'name_dutch': 'SURF',
                                'description_english': 'The collaborative ICT organization for Dutch education and research',
                                'description_dutch': 'De samenwerkingsorganisatie voor ICT in het onderwijs en onderzoek',
                                'entity_id': 'NiqkZiz2TaGT8B4RRwG8Fg',
                                'created_at': '2025-01-15T10:00:00.000000',
                                'image_english': 'uploads/institution/surf_logo_en.png',
                                'image_dutch': 'uploads/institution/surf_logo_nl.png',
                                'brin': '27KP',
                                'grading_table': 'uploads/grading/surf_grading_table.pdf',
                                'eppn_reg_exp_format': '^[a-zA-Z0-9._%+-]+@surf\\.nl$',
                                'admins': [
                                    {'email': 'admin1@surf.nl', 'name': 'Jan de Vries'},
                                    {'email': 'admin2@surf.nl', 'name': 'Maria Jansen'},
                                ],
                            },
                            'permissions': {
                                'ins_may_create': 1,
                                'f_may_create': 1,
                                'fac_count': 5,
                            },
                        },
                    ),
                    OpenApiExample(
                        'No institution',
                        description='Returns empty objects when user has no institution',
                        response_only=True,
                        value={'current_institution': {}, 'permissions': {}},
                    ),
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='Your email address must be verified to access this resource.'
            ),
        },
    )
    def get(self, request, **kwargs):
        if not request.user.institution:
            return Response({'current_institution': {}, 'permissions': {}}, status=status.HTTP_200_OK)

        with connection.cursor() as cursor:
            cursor.execute(
                """
    select ins.id, ins.name_english, ins.name_dutch, ins.description_english, ins.description_dutch, ins.entity_id,
            ins.created_at, ins.image_english, ins.image_dutch, ins.brin, ins.grading_table, ins.eppn_reg_exp_format,
            u.email, u.first_name, u.last_name
    from institution_institution ins
    left join staff_institutionstaff sta_ins on sta_ins.institution_id = ins.id
    left join users u on u.id =  sta_ins.user_id           
    where ins.id = %(ins_id)s order by ins.id
                """,
                {'ins_id': request.user.institution.id if request.user.institution else None},
            )
            records = dict_fetch_all(cursor)
            if not records:
                return Response({'current_institution': {}, 'permissions': {}}, status=status.HTTP_200_OK)
            current_institution = records[0]
            current_institution['admins'] = [
                {'email': u['email'], 'name': f'{u["first_name"]} {u["last_name"]}'} for u in records
            ]
            for attr in ['email', 'first_name', 'last_name']:
                del current_institution[attr]

                cursor.execute(
                    """
            select sta_ins.may_create as ins_may_create, facst.may_create as f_may_create,
                (select count(id) from institution_faculty where institution_id = %(insitution_id)s) as fac_count
                from staff_institutionstaff sta_ins
                left join users u on u.id = sta_ins.user_id
                left join staff_facultystaff facst on facst.user_id = u.id
            where u.id = %(user_id)s 
                        """,
                    {'user_id': request.user.id, 'insitution_id': request.user.institution.id},
                )
            institution_permissions = dict_fetch_all(cursor)
            result = {
                'current_institution': current_institution,
                'permissions': institution_permissions[0] if institution_permissions else {},
            }
            return Response(result, status=status.HTTP_200_OK)


class CatalogBadgeClasses(APIView):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        methods=['GET'],
        description='Get badge classes',
        responses={
            200: OpenApiResponse(
                description='Successful responses with examples',
                response=dict,  # or inline custom serializer class
                examples=[
                    OpenApiExample(
                        'Two badge classes ',
                        description='Returns two badge classes',
                        response_only=True,
                        value=[
                            {
                                'createdAt': '2025-05-02T12:20:51.573423',
                                'name': 'Edubadge account complete',
                                'image': 'uploads/badges/edubadge_student.png',
                                'archived': 0,
                                'entityId': 'qNGehQ2dRTKyjNtiDvhWsQ',
                                'isPrivate': 0,
                                'isMicroCredentials': 0,
                                'typeBadgeClass': 'regular',
                                'i_name_english': 'Team edubadges',
                                'i_name_dutch': 'Team edubadges',
                                'i_entity_id': 'WOLxSjpWQouas1123Z809Q',
                                'i_image_dutch': '',
                                'i_image_english': 'uploads/issuers/surf.png',
                                'f_name_english': 'eduBadges',
                                'f_name_dutch': 'null',
                                'f_entity_id': 'lVu1kbaqSDyJV_1Bu8_bcw',
                                'f_image_dutch': '',
                                'f_image_english': '',
                                'onBehalfOf': 0,
                                'facultyType': 'null',
                                'ins_name_english': 'SURF',
                                'ins_name_dutch': 'SURF',
                                'ins_entity_id': 'NiqkZiz2TaGT8B4RRwG8Fg',
                                'ins_image_dutch': 'uploads/issuers/surf.png',
                                'ins_image_english': 'uploads/issuers/surf.png',
                                'institutionType': 'null',
                                'selfRequestedAssertionsCount': 1,
                                'directAwardedAssertionsCount': 0,
                            },
                            {
                                'createdAt': '2025-05-02T12:20:57.914064',
                                'name': 'Growth and Development',
                                'image': 'uploads/badges/eduid.png',
                                'archived': 0,
                                'entityId': 'Ge4D7gf1RLGYNZlSiCv-qA',
                                'isPrivate': 0,
                                'isMicroCredentials': 0,
                                'typeBadgeClass': 'regular',
                                'i_name_english': 'Medicine',
                                'i_name_dutch': 'null',
                                'i_entity_id': 'yuflXDK8ROukQkxSPmh5ag',
                                'i_image_dutch': '',
                                'i_image_english': 'uploads/issuers/surf.png',
                                'f_name_english': 'Medicine',
                                'f_name_dutch': 'null',
                                'f_entity_id': 'yYPphJ3bS5qszI7P69degA',
                                'f_image_dutch': '',
                                'f_image_english': '',
                                'onBehalfOf': 0,
                                'facultyType': 'null',
                                'ins_name_english': 'university-example.org',
                                'ins_name_dutch': 'null',
                                'ins_entity_id': '5rZhvRonT3OyyLQhhmuPmw',
                                'ins_image_dutch': 'uploads/institution/surf.png',
                                'ins_image_english': 'uploads/institution/surf.png',
                                'institutionType': 'WO',
                                'selfRequestedAssertionsCount': 0,
                                'directAwardedAssertionsCount': 0,
                            },
                        ],
                    )
                ],
            ),
            500: OpenApiResponse(
                description='Internal server error occurred while retrieving badge classes.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select bc.created_at as createdAt, bc.name, bc.image, bc.archived, bc.entity_id as entityId,
        bc.is_private as isPrivate, bc.is_micro_credentials as isMicroCredentials,
        bc.badge_class_type as typeBadgeClass,
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id,
        i.image_dutch as i_image_dutch, i.image_english as i_image_english, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        f.image_dutch as f_image_dutch, f.image_english as f_image_english,
        f.on_behalf_of as onBehalfOf, f.faculty_type as facultyType,
        ins.name_english as ins_name_english, ins.name_dutch as ins_name_dutch, ins.entity_id as ins_entity_id,
        ins.image_dutch as ins_image_dutch, ins.image_english as ins_image_english,
        ins.institution_type as institutionType,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'requested') as selfRequestedAssertionsCount,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'direct_award') as directAwardedAssertionsCount
from  issuer_badgeclass bc
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where  bc.is_private = 0 and f.archived = 0 and i.archived = 0 and (f.visibility_type <> 'TEST' OR f.visibility_type IS NULL);
            """,
                {},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class IssuersOverview(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get issuers',
        responses={
            200: OpenApiResponse(
                description='Successful responses with examples',
                response=dict,  # or inline custom serializer class
                examples=[
                    OpenApiExample(
                        'Two badge issuers',
                        description='Returns two issuers',
                        response_only=True,
                        value=[
                            {
                                'image_dutch': 'uploads/issuers/issuer_logo_3cce4cd0-a89d-4787-baca-48cbc1debb57.png',
                                'image_english': '',
                                'name_dutch': 'Spatial design',
                                'name_english': 'null',
                                'archived': 0,
                                'entityId': 'v4hexkBJQdyoTocmgBpc6g',
                                'f_name_english': '',
                                'f_name_dutch': 'Mediavormgeven',
                                'f_entity_id': 'ITRvICTuSRuAadlvsH1xbg',
                                'assertionCount': 1,
                                'badgeclassCount': 1,
                                'pendingEnrollmentCount': 0,
                                'may_create': 1,
                            },
                            {
                                'image_dutch': '',
                                'image_english': '',
                                'name_dutch': 'Sector Techniek',
                                'name_english': 'null',
                                'archived': 0,
                                'entityId': '19slRNF3RBuk83LjmbcUCA',
                                'f_name_english': 'null',
                                'f_name_dutch': 'Saxion Parttime School',
                                'f_entity_id': 'JZRc7GLKQn-Q7861-7f-ow',
                                'assertionCount': 0,
                                'badgeclassCount': 1,
                                'pendingEnrollmentCount': 0,
                                'may_create': 1,
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access issuers.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select i.name_dutch as nameDutch, i.name_english as nameEnglish, i.entity_id as entityId,
    f.faculty_type as facultyType
from  issuer_issuer i
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s and 
(
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_award = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_award = 1))
    or
    (exists (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = %(u_id)s and issst.may_award = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s and us.is_superuser = 1))
)
""",
                {'ins_id': request.user.institution.id, 'u_id': request.user.id},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class Issuers(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get all issuers for the current user's institution with badge class counts, assertion counts, "
        'pending enrollments, and user creation permissions.',
        responses={
            200: OpenApiResponse(
                description='List of issuers with statistics and faculty information',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Two issuers with statistics',
                        description='Returns issuers with counts and permissions',
                        response_only=True,
                        value=[
                            {
                                'image_dutch': 'uploads/issuers/education_dept_nl.png',
                                'image_english': 'uploads/issuers/education_dept_en.png',
                                'name_dutch': 'Opleidingskunde',
                                'name_english': 'Educational Sciences',
                                'archived': 0,
                                'entityId': 'Rst789Uvw012Xyz345Abc678',
                                'f_name_english': 'Faculty of Behavioral Sciences',
                                'f_name_dutch': 'Faculteit der Gedragswetenschappen',
                                'f_entity_id': 'Def901Ghi234Jkl567Mno890',
                                'assertionCount': 45,
                                'badgeclassCount': 8,
                                'pendingEnrollmentCount': 2,
                                'may_create': 1,
                            },
                            {
                                'image_dutch': '',
                                'image_english': 'uploads/issuers/engineering.png',
                                'name_dutch': 'Werktuigbouwkunde',
                                'name_english': 'Mechanical Engineering',
                                'archived': 0,
                                'entityId': 'Pqr123Stu456Vwx789Yza012',
                                'f_name_english': 'Faculty of Engineering',
                                'f_name_dutch': 'Faculteit der Techniek',
                                'f_entity_id': 'Bcd345Efg678Hij901Klm234',
                                'assertionCount': 103,
                                'badgeclassCount': 15,
                                'pendingEnrollmentCount': 7,
                                'may_create': 0,
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access issuers.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select i.image_dutch, i.image_english, i.name_dutch, i.name_english, i.archived, i.entity_id as entityId,
    f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
    (select count(id) from issuer_badgeinstance WHERE issuer_id = i.id) as assertionCount, 
    (select count(id) from issuer_badgeclass WHERE issuer_id = i.id) as badgeclassCount,
    (select count(*) from lti_edu_studentsenrolled l inner join issuer_badgeclass ib on ib.id = l.badge_class_id 
            WHERE ib.issuer_id = i.id and l.badge_instance_id IS NULL AND l.denied = 0) as pendingEnrollmentCount,
     (
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_create = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_create = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s  and us.is_superuser = 1))
) as may_create       
from  issuer_issuer i
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s and 
(
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_award = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_award = 1))
    or
    (exists (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = %(u_id)s and issst.may_award = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s and us.is_superuser = 1))
)
""",
                {'ins_id': request.user.institution.id, 'u_id': request.user.id},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class Faculties(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get all faculties for the current user's institution with issuer counts, pending enrollments, "
        'and user creation permissions.',
        responses={
            200: OpenApiResponse(
                description='List of faculties with statistics and metadata',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Two faculties',
                        description='Returns faculties with counts and permissions',
                        response_only=True,
                        value=[
                            {
                                'name_english': 'Faculty of Medicine',
                                'name_dutch': 'Faculteit der Geneeskunde',
                                'entityId': 'Nop567Qrs890Tuv123Wxy456',
                                'onBehalfOf': 0,
                                'image_dutch': 'uploads/faculty/medicine_nl.png',
                                'image_english': 'uploads/faculty/medicine_en.png',
                                'archived': 0,
                                'issuerCount': 12,
                                'pendingEnrollmentCount': 5,
                                'may_create': 1,
                            },
                            {
                                'name_english': 'Faculty of Law',
                                'name_dutch': 'Faculteit der Rechtsgeleerdheid',
                                'entityId': 'Zab789Cde012Fgh345Ijk678',
                                'onBehalfOf': 1,
                                'image_dutch': '',
                                'image_english': 'uploads/faculty/law.png',
                                'archived': 0,
                                'issuerCount': 7,
                                'pendingEnrollmentCount': 1,
                                'may_create': 0,
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access faculties.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(
                """
select f.name_english as name_english, f.name_dutch as name_dutch, f.entity_id as entityId, f.on_behalf_of as onBehalfOf,
    f.image_dutch, f.image_english, f.archived,
        (select count(id) from issuer_issuer WHERE faculty_id = f.id) as issuerCount,
    (select count(*) from lti_edu_studentsenrolled l 
            inner join issuer_badgeclass ib on ib.id = l.badge_class_id
            inner join issuer_issuer ii on ii.id = ib.issuer_id 
            WHERE ii.faculty_id = f.id and l.badge_instance_id IS NULL AND l.denied = 0) as pendingEnrollmentCount,
     (
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_create = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s  and us.is_superuser = 1))
    ) as may_create       
from  institution_faculty f
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s and 
(
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = %(u_id)s and insst.may_award = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = %(u_id)s and facst.may_award = 1))
    or
    (exists (select 1 from users us where us.id = %(u_id)s and us.is_superuser = 1))
)
""",
                {'ins_id': request.user.institution.id, 'u_id': request.user.id},
            )
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


user_categories = [
    {'prefix': 'ins', 'permission': 'institution', 'weight': 1, 'identifier': 'institution_id'},
    {'prefix': 'f', 'permission': 'faculty', 'weight': 2, 'identifier': 'faculty_id'},
    {'prefix': 'i', 'permission': 'issuer', 'weight': 3, 'identifier': 'issuer_id'},
    {'prefix': 'bc', 'permission': 'badge_class', 'weight': 4, 'identifier': 'badgeclass_id'},
]


def remove_duplicate_permissions(row):
    unique_permissions = []
    seen = set()
    for permission in row['permissions']:
        key = (permission['permission'], permission['identifier'])  # Use tuple of attributes as key
        if key not in seen:
            seen.add(key)
            unique_permissions.append(permission)
    if unique_permissions:
        min(unique_permissions, key=lambda x: x['weight'])['highest'] = True
    row['permissions'] = unique_permissions


def parse_unit(row, source_prefix, unit_prefix, use_prefix):
    prefix = f'{source_prefix}_{unit_prefix}' if use_prefix else f'{unit_prefix}'
    return {
        'name_english': row.get(f'{prefix}_name_english'),
        'name_dutch': row.get(f'{prefix}_name_dutch'),
        'entity_id': row.get(f'{prefix}_entity_id'),
    }


def permissions(row, use_prefix=True):
    all_permissions = []
    for category in user_categories:
        prefix = category['prefix']
        may_update = row.get(f'{prefix}_may_update')
        may_award = row.get(f'{prefix}_may_award')
        may_administrate = row.get(f'{prefix}_may_admin')
        if may_update or may_award or may_administrate:
            permission_type = category['permission']
            permission_ = {
                'permission': permission_type,
                'weight': category['weight'],
                'level': 'admin' if may_administrate else 'editor' if may_update else 'awarder',
                'identifier': row.get(category['identifier']),
                'institution': parse_unit(row, prefix, 'ins', use_prefix),
            }
            if use_prefix:
                if prefix != 'ins':
                    permission_['faculty'] = parse_unit(row, prefix, 'f', use_prefix)
                    if prefix != 'f':
                        permission_['issuer'] = parse_unit(row, prefix, 'i', use_prefix)
                        if prefix != 'i':
                            permission_['badge_class'] = parse_unit(row, prefix, 'bc', use_prefix)
            else:
                permission_[permission_type] = parse_unit(row, None, prefix, False)
            all_permissions.append(permission_)
    return all_permissions


class Users(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get all users with their permissions for the current user's institution. "
        'Superusers can optionally retrieve users from all institutions using the "all" query parameter.',
        parameters=[
            OpenApiParameter(
                name='all',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='If true and user is superuser, retrieve users from all institutions (default: false)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='List of users with their institutional permissions at various levels',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Users with permissions',
                        description='Returns users with hierarchical permissions',
                        response_only=True,
                        value=[
                            {
                                'id': 123,
                                'first_name': 'Anna',
                                'last_name': 'Visser',
                                'email': 'a.visser@university-example.nl',
                                'entity_id': 'Lmn901Opq234Rst567Uvw890',
                                'institution_entity_id': 'Xyz345Abc678Def901Ghi234',
                                'institution_name_english': 'University of Amsterdam',
                                'institution_name_dutch': 'Universiteit van Amsterdam',
                                'permissions': [
                                    {
                                        'permission': 'faculty',
                                        'weight': 2,
                                        'level': 'editor',
                                        'identifier': 45,
                                        'institution': {
                                            'name_english': 'University of Amsterdam',
                                            'name_dutch': 'Universiteit van Amsterdam',
                                            'entity_id': 'Xyz345Abc678Def901Ghi234',
                                        },
                                        'faculty': {
                                            'name_english': 'Faculty of Science',
                                            'name_dutch': 'Faculteit der Exacte Wetenschappen',
                                            'entity_id': 'Jkl567Mno890Pqr123Stu456',
                                        },
                                        'highest': True,
                                    }
                                ],
                            },
                            {
                                'id': 456,
                                'first_name': 'Peter',
                                'last_name': 'de Boer',
                                'email': 'p.deboer@university-example.nl',
                                'entity_id': 'Vwx789Yza012Bcd345Efg678',
                                'institution_entity_id': 'Xyz345Abc678Def901Ghi234',
                                'institution_name_english': 'University of Amsterdam',
                                'institution_name_dutch': 'Universiteit van Amsterdam',
                                'permissions': [
                                    {
                                        'permission': 'badge_class',
                                        'weight': 4,
                                        'level': 'awarder',
                                        'identifier': 89,
                                        'institution': {
                                            'name_english': 'University of Amsterdam',
                                            'name_dutch': 'Universiteit van Amsterdam',
                                            'entity_id': 'Xyz345Abc678Def901Ghi234',
                                        },
                                        'faculty': {
                                            'name_english': 'Faculty of Humanities',
                                            'name_dutch': 'Faculteit der Geesteswetenschappen',
                                            'entity_id': 'Hij901Klm234Nop567Qrs890',
                                        },
                                        'issuer': {
                                            'name_english': 'Dutch Language & Culture',
                                            'name_dutch': 'Nederlandse Taal en Cultuur',
                                            'entity_id': 'Tuv123Wxy456Zab789Cde012',
                                        },
                                        'badge_class': {
                                            'name_english': 'Dutch Literature',
                                            'name_dutch': 'Nederlandse Literatuur',
                                            'entity_id': 'Fgh345Ijk678Lmn901Opq234',
                                        },
                                        'highest': True,
                                    }
                                ],
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access user information.'
            ),
        },
    )
    def get(self, request, **kwargs):
        all_institutions = request.GET.get('all')
        filter_by_institution = True
        if all_institutions and hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            filter_by_institution = False

        with connection.cursor() as cursor:
            query_ = """
SELECT u.id, u.email, u.first_name, u.last_name, u.entity_id, 
        institution.entity_id as institution_entity_id, 
        institution.name_english as institution_name_english, 
        institution.name_dutch as institution_name_dutch,
    ins.may_update as ins_may_update, ins.institution_id,
        ins.name_english as ins_ins_name_english, ins.name_dutch as ins_ins_name_dutch, ins.entity_id as ins_ins_entity_id,
    f.may_update as f_may_update, f.may_award as f_may_award, f.may_administrate_users as f_may_admin, f.faculty_id,
        f.name_dutch as f_f_name_dutch, f.name_english as f_f_name_english, f.entity_id as f_f_entity_id, 
        f.ins_entity_id as f_ins_entity_id, f.ins_name_dutch as f_ins_name_dutch, f.ins_name_english as f_ins_name_english,
    i.may_update as i_may_update, i.may_award as i_may_award, i.may_administrate_users as i_may_admin, i.issuer_id,
        i.entity_id as i_i_entity_id, i.name_dutch as i_i_name_dutch, i.name_english as i_i_name_english,
        i.f_name_dutch as i_f_name_dutch, i.f_name_english as i_f_name_english, i.f_entity_id as i_f_entity_id, 
        i.ins_entity_id as i_ins_entity_id, i.ins_name_dutch as i_ins_name_dutch, i.ins_name_english as i_ins_name_english,
    bc.may_update as bc_may_update, bc.may_award as bc_may_award, bc.may_administrate_users as bc_may_admin, bc.badgeclass_id,
        bc.name as bc_bc_name_dutch, bc.name as bc_bc_name_english, bc.entity_id as bc_bc_entity_id, 
        bc.i_entity_id as bc_i_entity_id, bc.i_name_dutch as bc_i_name_dutch, bc.i_name_english as bc_i_name_english,
        bc.f_name_dutch as bc_f_name_dutch, bc.f_name_english as bc_f_name_english, bc.f_entity_id as bc_f_entity_id, 
        bc.ins_entity_id as bc_ins_entity_id, bc.ins_name_dutch as bc_ins_name_dutch, bc.ins_name_english as bc_ins_name_english
    FROM users u INNER JOIN institution_institution institution ON u.institution_id = institution.id
    LEFT JOIN (
        SELECT st_in.may_update, st_in.user_id, st_in.institution_id, 
            ins.name_english, ins.name_dutch, ins.entity_id
        FROM staff_institutionstaff st_in
            INNER JOIN institution_institution ins ON st_in.institution_id = ins.id
    ) ins ON (u.id = ins.user_id)
    LEFT JOIN (
        SELECT st_fa.may_update, st_fa.may_award, st_fa.may_administrate_users, st_fa.user_id, st_fa.faculty_id,
            fac.name_english, fac.name_dutch, fac.entity_id,
            ins.name_english as ins_name_english, ins.name_dutch as ins_name_dutch, ins.entity_id as ins_entity_id
        FROM staff_facultystaff st_fa
            INNER JOIN institution_faculty fac ON st_fa.faculty_id = fac.id
            INNER JOIN institution_institution ins ON fac.institution_id = ins.id            
    ) f ON (u.id = f.user_id)
    LEFT JOIN (
        SELECT st_is.may_update, st_is.may_award, st_is.may_administrate_users, st_is.user_id, st_is.issuer_id,
            iss_iss.name_english, iss_iss.name_dutch, iss_iss.entity_id,
            fac.name_english as f_name_english, fac.name_dutch as f_name_dutch, fac.entity_id as f_entity_id,
            ins.name_english as ins_name_english, ins.name_dutch as ins_name_dutch, ins.entity_id as ins_entity_id
        FROM staff_issuerstaff st_is
            INNER JOIN issuer_issuer iss_iss ON iss_iss.id = st_is.issuer_id 
            INNER JOIN institution_faculty fac ON iss_iss.faculty_id = fac.id
            INNER JOIN institution_institution ins ON fac.institution_id = ins.id
    ) i ON (u.id = i.user_id)
    LEFT JOIN (
        SELECT st_bc.may_update, st_bc.may_award, st_bc.may_administrate_users, st_bc.user_id, st_bc.badgeclass_id,
            ib.name, ib.entity_id,
            iss_iss.name_english as i_name_english, iss_iss.name_dutch as i_name_dutch, iss_iss.entity_id as i_entity_id,
            fac.name_english as f_name_english, fac.name_dutch as f_name_dutch, fac.entity_id as f_entity_id,
            ins.name_english as ins_name_english, ins.name_dutch as ins_name_dutch, ins.entity_id as ins_entity_id
        FROM staff_badgeclassstaff st_bc  
            INNER JOIN issuer_badgeclass ib ON ib.id = st_bc.badgeclass_id
            INNER JOIN issuer_issuer iss_iss ON iss_iss.id = ib.issuer_id 
            INNER JOIN institution_faculty fac ON iss_iss.faculty_id = fac.id
            INNER JOIN institution_institution ins ON fac.institution_id = ins.id
    ) bc ON (u.id = bc.user_id) where u.institution_id = COALESCE(%(ins_id)s, u.institution_id)"""
            cursor.execute(query_, {"ins_id": request.user.institution.id if filter_by_institution else None})
            users = dict_fetch_all(cursor)

            users_dict = {}
            for r in users:
                user_id = r['id']
                if user_id not in users_dict:
                    users_dict[user_id] = {
                        'id': user_id,
                        'first_name': r['first_name'],
                        'last_name': r['last_name'],
                        'email': r['email'],
                        'entity_id': r['entity_id'],
                        'institution_entity_id': r['institution_entity_id'],
                        'institution_name_english': r['institution_name_english'],
                        'institution_name_dutch': r['institution_name_dutch'],
                        'permissions': [],
                    }
                user_permissions = permissions(r)
                if user_permissions:
                    users_dict[user_id]['permissions'].extend(user_permissions)

            users_with_permissions = list(users_dict.values())
            for u in users_with_permissions:
                remove_duplicate_permissions(u)

            return Response(users_with_permissions, status=status.HTTP_200_OK)


class Notifications(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get badge classes with notification status for the current user. Returns active (non-archived) '
        'badge classes where the user has permissions, including whether notifications are enabled.',
        responses={
            200: OpenApiResponse(
                description='List of badge classes with notification status and user permissions',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Badge classes with notifications',
                        description='Returns badge classes with notification settings',
                        response_only=True,
                        value=[
                            {
                                'name_english': 'Project Management',
                                'bc_entity_id': 'Rst567Uvw890Xyz123Abc456',
                                'badgeclass_id': 67,
                                'image': 'uploads/badges/project_mgmt.png',
                                'f_name_dutch': 'Bedrijfskunde',
                                'f_name_english': 'Business Administration',
                                'f_entity_id': 'Def789Ghi012Jkl345Mno678',
                                'faculty_id': 23,
                                'i_entity_id': 'Pqr901Stu234Vwx567Yza890',
                                'i_name_dutch': 'Management Studies',
                                'i_name_english': 'Management Studies',
                                'issuer_id': 34,
                                'ins_entity_id': 'Bcd123Efg456Hij789Klm012',
                                'ins_name_dutch': 'Rotterdam School of Management',
                                'ins_name_english': 'Rotterdam School of Management',
                                'institution_id': 12,
                                'nbc_badgeclass_id': 67,
                                'ins_may_update': None,
                                'f_may_update': None,
                                'f_may_award': 1,
                                'f_may_administrate_users': None,
                                'i_may_update': None,
                                'i_may_award': None,
                                'i_may_administrate_users': None,
                                'bc_may_update': None,
                                'bc_may_award': None,
                                'bc_may_administrate_users': None,
                                'permissions': [
                                    {
                                        'permission': 'faculty',
                                        'weight': 2,
                                        'level': 'awarder',
                                        'identifier': 23,
                                        'faculty': {
                                            'name_english': 'Business Administration',
                                            'name_dutch': 'Bedrijfskunde',
                                            'entity_id': 'Def789Ghi012Jkl345Mno678',
                                        },
                                        'highest': True,
                                    }
                                ],
                            },
                            {
                                'name_english': 'Digital Marketing',
                                'bc_entity_id': 'Nop345Qrs678Tuv901Wxy234',
                                'badgeclass_id': 72,
                                'image': 'uploads/badges/digital_marketing.png',
                                'f_name_dutch': 'Communicatiewetenschappen',
                                'f_name_english': 'Communication Sciences',
                                'f_entity_id': 'Zab567Cde890Fgh123Ijk456',
                                'faculty_id': 18,
                                'i_entity_id': 'Lmn789Opq012Rst345Uvw678',
                                'i_name_dutch': 'Marketing',
                                'i_name_english': 'Marketing',
                                'issuer_id': 41,
                                'ins_entity_id': 'Bcd123Efg456Hij789Klm012',
                                'ins_name_dutch': 'Rotterdam School of Management',
                                'ins_name_english': 'Rotterdam School of Management',
                                'institution_id': 12,
                                'nbc_badgeclass_id': None,
                                'ins_may_update': None,
                                'f_may_update': None,
                                'f_may_award': None,
                                'f_may_administrate_users': None,
                                'i_may_update': 1,
                                'i_may_award': None,
                                'i_may_administrate_users': None,
                                'bc_may_update': None,
                                'bc_may_award': None,
                                'bc_may_administrate_users': None,
                                'permissions': [
                                    {
                                        'permission': 'issuer',
                                        'weight': 3,
                                        'level': 'editor',
                                        'identifier': 41,
                                        'faculty': {
                                            'name_english': 'Communication Sciences',
                                            'name_dutch': 'Communicatiewetenschappen',
                                            'entity_id': 'Zab567Cde890Fgh123Ijk456',
                                        },
                                        'issuer': {
                                            'name_english': 'Marketing',
                                            'name_dutch': 'Marketing',
                                            'entity_id': 'Lmn789Opq012Rst345Uvw678',
                                        },
                                        'highest': True,
                                    }
                                ],
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access notification settings.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            query_ = f"""
            select bc.name as name_english, bc.entity_id as bc_entity_id, bc.id as badgeclass_id, bc.image,
f.name_dutch as f_name_dutch, f.name_english as f_name_english, f.entity_id as f_entity_id, f.id as faculty_id,
i.entity_id as i_entity_id, i.name_dutch as i_name_dutch, i.name_english as i_name_english, i.id as issuer_id,
ins.entity_id as ins_entity_id, ins.name_dutch as ins_name_dutch, ins.name_english as ins_name_english, ins.id as institution_id,
nbc.badgeclass_id as nbc_badgeclass_id,
st_in.may_update as ins_may_update,
st_fa.may_update as f_may_update,
st_fa.may_award as f_may_award,
st_fa.may_administrate_users as f_may_administrate_users,
st_is.may_update as i_may_update,
st_is.may_award as i_may_award,
st_is.may_administrate_users as i_may_administrate_users,
st_bc.may_update as bc_may_update,
st_bc.may_award as bc_may_award,
st_bc.may_administrate_users as bc_may_administrate_users
from  issuer_badgeclass bc
left join notifications_badgeclassusernotification nbc on nbc.badgeclass_id = bc.id and nbc.user_id = %(u_id)s
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
LEFT JOIN staff_institutionstaff st_in ON st_in.institution_id = ins.id AND st_in.user_id = %(u_id)s
LEFT JOIN staff_facultystaff st_fa ON st_fa.faculty_id = f.id AND st_fa.user_id = %(u_id)s
LEFT JOIN staff_issuerstaff st_is ON st_is.issuer_id = i.id and st_is.user_id = %(u_id)s
LEFT JOIN staff_badgeclassstaff st_bc ON st_bc.badgeclass_id = bc.id AND st_bc.user_id = %(u_id)s
where ins.id = %(ins_id)s and bc.archived = 0 and {permissions_query} 
"""
            cursor.execute(query_, {'u_id': request.user.id, 'ins_id': request.user.institution.id})
            notifications = dict_fetch_all(cursor)

            for r in notifications:
                user_permissions = permissions(r, False)
                if user_permissions:
                    r['permissions'] = user_permissions
                    remove_duplicate_permissions(r)
            return Response(notifications, status=status.HTTP_200_OK)


class EndorsementBadgeClasses(APIView):
    permission_classes = (TeachPermission,)

    @extend_schema(
        methods=['GET'],
        description="Get active (non-archived) badge classes available for endorsement within the current user's institution. "
        'Returns badge classes where the user has appropriate permissions.',
        responses={
            200: OpenApiResponse(
                description='List of badge classes eligible for endorsement',
                response=dict,
                examples=[
                    OpenApiExample(
                        'Badge classes for endorsement',
                        description='Returns badge classes that can be endorsed',
                        response_only=True,
                        value=[
                            {
                                'name': 'Advanced Statistics',
                                'entityId': 'Wxy901Zab234Cde567Fgh890',
                                'badgeclass_id': 78,
                                'image': 'uploads/badges/statistics_advanced.png',
                                'institution_entity_id': 'Ijk123Lmn456Opq789Rst012',
                                'institution_id': 15,
                            },
                            {
                                'name': 'Leadership Skills',
                                'entityId': 'Uvw345Xyz678Abc901Def234',
                                'badgeclass_id': 82,
                                'image': 'uploads/badges/leadership.png',
                                'institution_entity_id': 'Ijk123Lmn456Opq789Rst012',
                                'institution_id': 15,
                            },
                            {
                                'name': 'Research Ethics',
                                'entityId': 'Ghi567Jkl890Mno123Pqr456',
                                'badgeclass_id': 91,
                                'image': 'uploads/badges/ethics.png',
                                'institution_entity_id': 'Ijk123Lmn456Opq789Rst012',
                                'institution_id': 15,
                            },
                        ],
                    )
                ],
            ),
            401: OpenApiResponse(
                description='Authentication credentials were not provided or are invalid.'
            ),
            403: OpenApiResponse(
                description='You do not have teaching permissions required to access badge classes for endorsement.'
            ),
        },
    )
    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            query_ = f"""
            select bc.name, bc.entity_id as entityId, bc.id as badgeclass_id, bc.image,
            ins.entity_id as institution_entity_id, ins.id as institution_id
            from  issuer_badgeclass bc
            inner join issuer_issuer i on i.id = bc.issuer_id
            inner join institution_faculty f on f.id = i.faculty_id
            inner join institution_institution ins on ins.id = f.institution_id
            where ins.id = %(ins_id)s and bc.archived = 0 and {permissions_query} 
"""
            cursor.execute(query_, {'u_id': request.user.id, 'ins_id': request.user.institution.id})
            badge_classes = dict_fetch_all(cursor)

            return Response(badge_classes, status=status.HTTP_200_OK)
