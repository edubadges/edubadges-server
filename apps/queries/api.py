from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from mainsite.permissions import TeachPermission


def dict_fetch_all(cursor):
    desc = cursor.description
    rows = cursor.fetchall()
    res = [dict(zip([col[0] for col in desc], row)) for row in rows]
    return res


class DirectAwards(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):

        with connection.cursor() as cursor:
            cursor.execute("""
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
where ins.id = %(ins_id)s and
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
) ;
            """, {"ins_id": request.user.institution.id, "u_id": request.user.id})
            return Response(dict_fetch_all(cursor), status=status.HTTP_200_OK)
