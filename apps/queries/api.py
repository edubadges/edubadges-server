from itertools import groupby

from django.db import connection
from rest_framework import status
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
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        ins.name_english as ins_name_english, ins.name_dutch  as ins_name_dutch, ins.entity_id as ins_entity_id
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
select bc.created_at, bc.name, bc.image, bc.entity_id, bc.archived, bc.image, bc.entity_id as bc_entity_id,
        bc.badge_class_type,  bc.image,
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id,
        i.image_dutch as i_image_dutch, i.image_english as i_image_english, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        f.on_behalf_of, f.on_behalf_of_display_name, f.image_dutch as f_image_dutch, f.image_english as f_image_english,
        (SELECT GROUP_CONCAT(DISTINCT isbt.name) FROM institution_badgeclasstag isbt
        INNER JOIN issuer_badgeclass_tags ibt ON ibt.badgeclasstag_id = isbt.id
        WHERE ibt.badgeclass_id = bc.id) AS tags,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'requested') as count_requested,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'direct_award') as count_direct_award,
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
            ins.created_at, ins.image_english, ins.image_dutch,
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

    def get(self, request, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("""
select bc.created_at, bc.name, bc.image, bc.entity_id, bc.archived, bc.image, bc.entity_id as bc_entity_id,
        bc.badge_class_type, bc.image, 
        i.name_english as i_name_english, i.name_dutch as i_name_dutch, i.entity_id as i_entity_id,
        i.image_dutch as i_image_dutch, i.image_english as i_image_english, 
        f.name_english as f_name_english, f.name_dutch as f_name_dutch, f.entity_id as f_entity_id,
        f.on_behalf_of, f.on_behalf_of_display_name, f.image_dutch as f_image_dutch, f.image_english as f_image_english,
        (SELECT GROUP_CONCAT(DISTINCT isbt.name) FROM institution_badgeclasstag isbt
        INNER JOIN issuer_badgeclass_tags ibt ON ibt.badgeclasstag_id = isbt.id
        WHERE ibt.badgeclass_id = bc.id) AS tags,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'requested') as count_requested,
        (select count(id) from issuer_badgeinstance WHERE badgeclass_id = bc.id AND award_type = 'direct_award') as count_direct_award,
        (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = 2 and insst.may_award = 1) as ins_staff,
        (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = 2 and facst.may_award = 1) as fac_staff,
        (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = 2 and issst.may_award = 1) as iss_staff,
        (select 1 from staff_badgeclassstaff bcst where bcst.badgeclass_id = bc.id and bcst.user_id = 2 and bcst.may_award = 1) as bc_staff
from  issuer_badgeclass bc
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
where  bc.is_private = 0;
            """, {})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)
