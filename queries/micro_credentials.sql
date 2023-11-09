select b.id, b.name as badgeclass_name, i.name_english, f.name_english as faculty_name, ins.name_english as institution_name, ins.identifier, b.created_at ,
(select original_json from issuer_badgeclassextension where name = 'extensions:EQFExtension' and badgeclass_id = b.id limit 1) as eqf_value,
(select original_json from issuer_badgeclassextension where name = 'extensions:StudyLoadExtension' and badgeclass_id = b.id limit 1) as study_load
 from issuer_badgeclass b
 inner join issuer_issuer i on i.id = b.issuer_id
 inner join institution_faculty f on f.id = i.faculty_id
 inner join institution_institution ins on ins.id = f.institution_id
 where b.is_micro_credentials = 1 and ins.institution_type is not null;