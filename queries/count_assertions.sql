select ins.identifier, count(u.id) as user_count, (select count(bi.id) from issuer_badgeinstance bi where bi.user_id = u.id ) as assertion_count
from users u
 inner join issuer_badgeinstance bi on bi.user_id = u.id
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 inner join issuer_issuer i on i.id = b.issuer_id
 inner join institution_faculty f on f.id = i.faculty_id
 inner join institution_institution ins on ins.id = f.institution_id
 where b.is_micro_credentials = 1 and ins.institution_type is not null
 group by assertion_count, ins.identifier
 order by ins.identifier ;

select count(bi.id), b.badge_class_type, b.archived from issuer_badgeinstance bi
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 group by b.badge_class_type, b.archived;