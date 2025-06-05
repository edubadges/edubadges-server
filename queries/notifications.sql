select bc.id, bc.name, bc.entity_id as bc_entity_id,
f.name_dutch as f_name_dutch, f.name_english as f_name_english, f.entity_id as f_entity_id,
i.entity_id as i_entity_id, i.name_dutch as i_name_dutch, i.name_english as i_name_english,
(select badgeclass_id from notifications_badgeclassusernotification WHERE badgeclass_id = bc.id and user_id = 2) as nbc_badgeclass_id,
(select may_update from staff_facultystaff WHERE faculty_id = f.id and user_id = 2) as f_may_update,
(select may_award from staff_facultystaff WHERE faculty_id = f.id and user_id = 2) as f_may_award
from  issuer_badgeclass bc
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
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

select bc.name, bc.entity_id as bc_entity_id, bc.id as bc_id,
f.name_dutch as f_name_dutch, f.name_english as f_name_english, f.entity_id as f_entity_id,
i.entity_id as i_entity_id, i.name_dutch as i_name_dutch, i.name_english as i_name_english,
nbc.badgeclass_id as nbc_badgeclass_id,
st_in.may_update as i_may_update,
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
    LEFT JOIN (
        SELECT st_in.may_update, st_in.user_id
        FROM staff_institutionstaff st_in
            INNER JOIN institution_institution ins ON st_in.institution_id = ins.id
    ) st_in ON st_in.user_id = 2
    LEFT JOIN (
        SELECT st_fa.may_update, st_fa.may_award, st_fa.may_administrate_users, st_fa.user_id, st_fa.faculty_id
        FROM staff_facultystaff st_fa
            INNER JOIN institution_faculty fac ON st_fa.faculty_id = fac.id
    ) st_fa ON st_fa.user_id = 2
    LEFT JOIN (
        SELECT st_is.may_update, st_is.may_award, st_is.may_administrate_users, st_is.user_id, st_is.issuer_id
        FROM staff_issuerstaff st_is
            INNER JOIN issuer_issuer i ON st_is.issuer_id = i.id
    ) st_is ON st_is.user_id = 2
    LEFT JOIN (
        SELECT st_bc.may_update, st_bc.may_award, st_bc.may_administrate_users, st_bc.user_id, st_bc.badgeclass_id
        FROM staff_badgeclassstaff st_bc
            INNER JOIN issuer_badgeclass ib ON ib.id = st_bc.badgeclass_id
    ) st_bc ON st_bc.user_id = 2
left join notifications_badgeclassusernotification nbc on nbc.badgeclass_id = bc.id and nbc.user_id = 2
inner join issuer_issuer i on i.id = bc.issuer_id
inner join institution_faculty f on f.id = i.faculty_id
inner join institution_institution ins on ins.id = f.institution_id
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
