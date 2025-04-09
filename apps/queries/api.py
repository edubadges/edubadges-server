from django.db import connection
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from directaward.models import DirectAward
from mainsite.permissions import TeachPermission, AuthenticatedWithVerifiedEmail

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

    def get(self, request, **kwargs):
        unclaimed = request.GET.get("status", "unclaimed") == "unclaimed"
        status_param = [DirectAward.STATUS_UNACCEPTED, DirectAward.STATUS_SCHEDULED] if unclaimed else [
            DirectAward.STATUS_DELETED]
        with connection.cursor() as cursor:
            cursor.execute(f"""
select da.created_at, da.resend_at, da.delete_at, da.recipient_email as recipientEmail, da.eppn, da.entity_id as entityId,
        bc.name, bc.entity_id as bc_entity_id,
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id
from  directaward_directaward da
inner join issuer_badgeclass bc on bc.id = da.badgeclass_id
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where ins.id = %(ins_id)s and da.status in %(status)s and {permissions_query} ;
""", {"ins_id": request.user.institution.id, "u_id": request.user.id, "status": status_param})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class BadgeClasses(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
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
        (SELECT GROUP_CONCAT(DISTINCT isbt.name) FROM institution_badgeclasstag isbt
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
            """, {"ins_id": request.user.institution.id, "u_id": request.user.id})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class CurrentInstitution(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    def get(self, request, **kwargs):
        if not request.user.institution:
            return Response({"current_institution": {}, "permissions": {}}, status=status.HTTP_200_OK)

        with connection.cursor() as cursor:
            cursor.execute("""
    select ins.id, ins.name_english, ins.name_dutch, ins.description_english, ins.description_dutch,
            ins.created_at, ins.image_english, ins.image_dutch, ins.brin, ins.grading_table, ins.eppn_reg_exp_format,
            u.email, u.first_name, u.last_name
    from institution_institution ins
    left join staff_institutionstaff sta_ins on sta_ins.institution_id = ins.id
    left join users u on u.id =  sta_ins.user_id           
    where ins.id = %(ins_id)s order by ins.id
                """, {"ins_id": request.user.institution.id if request.user.institution else None})
            records = dict_fetch_all(cursor)
            if not records:
                return Response({"current_institution": {}, "permissions": {}}, status=status.HTTP_200_OK)
            current_institution = records[0]
            current_institution["admins"] = [{"email": u["email"], "name": f"{u['first_name']} {u['last_name']}"} for u
                                             in records]
            for attr in ["email", "first_name", "last_name"]:
                del current_institution[attr]

                cursor.execute("""
            select sta_ins.may_create as ins_may_create, facst.may_create as f_may_create,
                (select count(id) from institution_faculty where institution_id = %(insitution_id)s) as fac_count
                from staff_institutionstaff sta_ins
                left join users u on u.id = sta_ins.user_id
                left join staff_facultystaff facst on facst.user_id = u.id
            where u.id = %(user_id)s 
                        """, {"user_id": request.user.id, "insitution_id": request.user.institution.id})
            institution_permissions = dict_fetch_all(cursor)
            result = {"current_institution": current_institution,
                      "permissions": institution_permissions[0] if institution_permissions else {}}
            return Response(result, status=status.HTTP_200_OK)


class CatalogBadgeClasses(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
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
where  bc.is_private = 0 and (f.visibility_type <> 'TEST' OR f.visibility_type IS NULL);
            """, {})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class Issuers(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(f"""
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
""", {"ins_id": request.user.institution.id, "u_id": request.user.id})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


class Faculties(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute(f"""
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
""", {"ins_id": request.user.institution.id, "u_id": request.user.id})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)


user_categories = [
    {"prefix": "ins", "permission": "institution", "weight": 1, "identifier": "institution_id"},
    {"prefix": "f", "permission": "faculty", "weight": 2, "identifier": "faculty_id"},
    {"prefix": "i", "permission": "issuer", "weight": 3, "identifier": "issuer_id"},
    {"prefix": "bc", "permission": "badge_class", "weight": 4, "identifier": "badgeclass_id"}
]


def remove_duplicate_permissions(row):
    unique_permissions = []
    seen = set()
    for permission in row["permissions"]:
        key = (permission["permission"], permission["identifier"])  # Use tuple of attributes as key
        if key not in seen:
            seen.add(key)
            unique_permissions.append(permission)
    if unique_permissions:
        min(unique_permissions, key=lambda x: x["weight"])["highest"] = True
    row["permissions"] = unique_permissions


def parse_unit(row, source_prefix, unit_prefix, use_prefix):
    prefix = f"{source_prefix}_{unit_prefix}" if use_prefix else f"{unit_prefix}"
    return {
        "name_english": row.get(f"{prefix}_name_english"),
        "name_dutch": row.get(f"{prefix}_name_dutch"),
        "entity_id": row.get(f"{prefix}_entity_id")
    }


def permissions(row, use_prefix=True):
    all_permissions = []
    for category in user_categories:
        prefix = category["prefix"]
        may_update = row.get(f"{prefix}_may_update")
        may_award = row.get(f"{prefix}_may_award")
        may_administrate = row.get(f"{prefix}_may_admin")
        if may_update or may_award or may_administrate:
            permission_type = category["permission"]
            permission_ = {
                "permission": permission_type,
                "weight": category["weight"],
                "level": "admin" if may_administrate else "editor" if may_update else "awarder",
                "identifier": row.get(category["identifier"]),
                "institution": parse_unit(row, prefix, "ins", use_prefix)
            }
            if use_prefix:
                if prefix != "ins":
                    permission_["faculty"] = parse_unit(row, prefix, "f", use_prefix)
                    if prefix != "f":
                        permission_["issuer"] = parse_unit(row, prefix, "i", use_prefix)
                        if prefix != "i":
                            permission_["badge_class"] = parse_unit(row, prefix, "bc", use_prefix)
            else:
                permission_[permission_type] = parse_unit(row, None, prefix, False)
            all_permissions.append(permission_)
    return all_permissions


class Users(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        all_institutions = request.GET.get("all")
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
    ) bc ON (u.id = bc.user_id) where u.institution_id = IFNULL(%(ins_id)s, u.institution_id)"""
            cursor.execute(query_, {"ins_id": request.user.institution.id if filter_by_institution else None})
            users = dict_fetch_all(cursor)

            users_dict = {}
            for r in users:
                user_id = r["id"]
                if user_id not in users_dict:
                    users_dict[user_id] = {"id": user_id, "first_name": r["first_name"],
                                           "last_name": r["last_name"], "email": r["email"],
                                           "entity_id": r["entity_id"],
                                           "institution_entity_id": r["institution_entity_id"],
                                           "institution_name_english": r["institution_name_english"],
                                           "institution_name_dutch": r["institution_name_dutch"],
                                           "permissions": []}
                user_permissions = permissions(r)
                if user_permissions:
                    users_dict[user_id]["permissions"].extend(user_permissions)

            users_with_permissions = list(users_dict.values())
            for u in users_with_permissions:
                remove_duplicate_permissions(u)

            return Response(users_with_permissions, status=status.HTTP_200_OK)


class Notifications(APIView):
    permission_classes = (TeachPermission,)

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
            cursor.execute(query_, {"u_id": request.user.id, "ins_id": request.user.institution.id})
            notifications = dict_fetch_all(cursor)

            for r in notifications:
                user_permissions = permissions(r, False)
                if user_permissions:
                    r["permissions"] = user_permissions
                    remove_duplicate_permissions(r)
            return Response(notifications, status=status.HTTP_200_OK)
