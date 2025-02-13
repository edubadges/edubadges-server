from django.db import connection
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from directaward.models import DirectAward
from mainsite.permissions import TeachPermission

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
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
    select ins.id, ins.name_english, ins.name_dutch, ins.description_english, ins.description_dutch,
            ins.created_at, ins.image_english, ins.image_dutch, ins.brin, ins.grading_table,
            u.email, u.first_name, u.last_name
    from institution_institution ins
    left join staff_institutionstaff sta_ins on sta_ins.institution_id = ins.id
    left join users u on u.id =  sta_ins.user_id           
    where ins.id = %(ins_id)s order by ins.id
                """, {"ins_id": request.user.institution.id})
            records = dict_fetch_all(cursor)
            result = records[0]
            result["admins"] = [{"email": u["email"], "name": f"{u['first_name']} {u['last_name']}"} for u in records]
            for attr in ["email", "first_name", "last_name"]:
                del result[attr]
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
where  bc.is_private = 0;
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
            WHERE ib.issuer_id = i.id and l.badge_instance_id IS NULL) as pendingEnrollmentCount,
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
    f.image_dutch, f.image_english,
    (select count(id) from issuer_issuer WHERE faculty_id = f.id) as issuerCount,
    (select count(*) from lti_edu_studentsenrolled l inner join issuer_badgeclass ib on ib.id = l.badge_class_id
            inner join issuer_issuer ii on ii.faculty_id = f.id 
            WHERE ii.faculty_id = f.id and l.badge_instance_id IS NULL) as pendingEnrollmentCount,
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


class Users(APIView):
    permission_classes = (TeachPermission,)

    permission_badge_class = "badge_class"
    permission_issuer = "issuer"
    permission_faculty = "faculty"
    permission_institution = "institution"

    admin = "admin"
    editor = "editor"
    awarder = "awarder"

    @staticmethod
    def _parse_unit(row, prefix):
        return {
            "name_english": row[f"{prefix}_name_english"],
            "name_dutch": row[f"{prefix}_name_dutch"],
            "entity_id": row[f"{prefix}_entity_id"]
        }


    def _permission(self, row):
        categories = [
            {"prefix":"ins", "permission": Users.permission_institution},
            {"prefix": "f", "permission": Users.permission_faculty},
            {"prefix": "i", "permission": Users.permission_issuer},
            {"prefix": "bc", "permission": Users.permission_badge_class}
        ]
        for category in categories:
            prefix = category["prefix"]
            may_update = row.get(f"{prefix}_mayUpdate")
            may_award = row.get(f"{prefix}_mayAward")
            may_administrate = row.get(f"{prefix}_mayAdmin")
            if may_update or may_award or may_administrate:
                return {
                    "highest": True,
                    "permission": category["permission"],
                    "level": Users.admin if may_administrate else Users.editor if may_update else Users.awarder,
                    "faculty": self._parse_unit(row, "f"),
                    "issuer": self._parse_unit(row, "i")
                }
        return None

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            # TODO refactor into 4 queries which will have less results or 1 query with subqueries on staff where user_id with inner joins in the subquery
            # to avoid the left join's
            cursor.execute("""
    select u.id, u.first_name, u.last_name, u.email, u.entity_id,
        i.id as i_id, i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id,
        f.id as f_id, f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        bc.id as bc_id, bc.name as bc_name, bc.entity_id as bc_entity_id,
        sta_ins.may_update as ins_mayUpdate, sta_ins.may_award as ins_mayAward,
            sta_ins.may_administrate_users as ins_mayAdmin,
        sta_fac.may_update as f_mayUpdate, sta_fac.may_award as f_mayAward, 
            sta_fac.may_administrate_users as f_mayAdmin, sta_fac.faculty_id as sf_id,
        sta_iss.may_update as i_mayUpdate, sta_iss.may_award as i_mayAward,
            sta_iss.may_administrate_users as i_mayAdmin, sta_iss.issuer_id as si_id,
        sta_bc.may_update as bc_mayUpdate, sta_bc.may_award as bc_mayAward,
            sta_bc.may_administrate_users as bc_mayAdmin
        from users u
        inner join institution_institution ins on ins.id = u.institution_id
        inner join institution_faculty f on f.institution_id = ins.id
        inner join issuer_issuer i on i.faculty_id = f.id
        inner join issuer_badgeclass bc on bc.issuer_id = i.id
        left join staff_institutionstaff sta_ins on (sta_ins.user_id = u.id AND sta_ins.institution_id = ins.id)
        left join staff_facultystaff sta_fac on (sta_fac.user_id = u.id and sta_fac.faculty_id = f.id)
        left join staff_issuerstaff sta_iss on (sta_iss.user_id = u.id and sta_iss.issuer_id = i.id)
        left join staff_badgeclassstaff sta_bc on (sta_bc.user_id = u.id AND sta_bc.badgeclass_id = bc.id)
        where u.institution_id = %(ins_id)s  
        and (
            sta_ins.may_update is not null or sta_ins.may_award is not null or sta_ins.may_administrate_users is not null or 
            sta_fac.may_update is not null or sta_fac.may_award is not null or sta_fac.may_administrate_users is not null or 
            sta_iss.may_update is not null or sta_iss.may_award is not null or sta_iss.may_administrate_users is not null or
            sta_bc.may_update is not null or sta_bc.may_award is not null or sta_bc.may_administrate_users is not null  
        )
    """, {"ins_id": request.user.institution.id})
            records = dict_fetch_all(cursor)
            users_dict = {}
            for row in records:
                user_id = row["id"]
                if user_id not in users_dict:
                    users_dict[user_id] = {"id": user_id, "first_name": row["first_name"],
                                           "last_name": row["last_name"], "email": row["email"],
                                           "entity_id": row["entity_id"], "permissions": []}
                permission = self._permission(row)
                if permission:
                    users_dict[user_id]["permissions"].append(permission)

            return Response(users_dict.values(), status=status.HTTP_200_OK)
