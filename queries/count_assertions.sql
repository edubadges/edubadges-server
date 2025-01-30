select count(u.id) as user_count, (select count(bi.id) from issuer_badgeinstance bi where bi.user_id = u.id ) as assertion_count
from users u
 inner join issuer_badgeinstance bi on bi.user_id = u.id
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 group by assertion_count

select count(bi.id), b.badge_class_type, b.archived from issuer_badgeinstance bi
 inner join issuer_badgeclass b on b.id = bi.badgeclass_id
 group by b.badge_class_type, b.archived;

select u.email from users u where (u.validated_name is null OR u.validated_name = '') and u.is_teacher = 0
 and exists(
  SELECT 1
    FROM issuer_badgeinstance bi INNER JOIN issuer_badgeclass bc
    WHERE bi.user_id = u.id AND bc.name <> 'Edubadge account complete'
 );