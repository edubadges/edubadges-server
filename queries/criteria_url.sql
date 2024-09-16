
select ins.identifier, bc.id,bc.name, bc.criteria_url from issuer_badgeclass bc
 inner join issuer_issuer i on i.id = bc.issuer_id
 inner join institution_faculty f on f.id = i.faculty_id
 inner join institution_institution ins on ins.id = f.institution_id
 where (bc.criteria_text is not null and trim(bc.criteria_text) <> '') and (bc.criteria_url is not null and trim(bc.criteria_url) <> '');