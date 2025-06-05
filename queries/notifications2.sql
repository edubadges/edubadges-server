select bc.name, bc.entity_id as bc_entity_id, bc.id as badgeclass_id,
f.name_dutch as f_name_dutch, f.name_english as f_name_english, f.entity_id as f_entity_id, f.id as faculty_id,
i.entity_id as i_entity_id, i.name_dutch as i_name_dutch, i.name_english as i_name_english, i.id as issuer_id,
ins.id as institution_id,
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
left join notifications_badgeclassusernotification nbc on nbc.badgeclass_id = bc.id and nbc.user_id = 2
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
LEFT JOIN staff_institutionstaff st_in ON st_in.institution_id = ins.id AND st_in.user_id = 2
LEFT JOIN staff_facultystaff st_fa ON st_fa.faculty_id = f.id AND st_fa.user_id = 2
LEFT JOIN staff_issuerstaff st_is ON st_is.issuer_id = i.id and st_is.user_id = 2
LEFT JOIN staff_badgeclassstaff st_bc ON st_bc.badgeclass_id = bc.id AND st_bc.user_id = 2
where ins.id = 2 and bc.archived = 0 and
(
    (exists (select 1 from staff_institutionstaff insst where insst.institution_id = ins.id and insst.user_id = 2 and insst.may_award = 1))
    or
    (exists (select 1 from staff_facultystaff facst where facst.faculty_id = f.id and facst.user_id = 2 and facst.may_award = 1))
    or
    (exists (select 1 from staff_issuerstaff issst where issst.issuer_id = i.id and issst.user_id = 2 and issst.may_award = 1))
    or
    (exists (select 1 from staff_badgeclassstaff bcst where bcst.badgeclass_id = bc.id and bcst.user_id = 2 and bcst.may_award = 1))
    or
    (exists (select 1 from users us where us.id = 2 and us.is_superuser = 1))
)
