SELECT `issuer_badgeinstance`.`award_type`,
       `issuer_badgeinstance`.`badgeclass_id`,
       `issuer_badgeclass`.`name`,
       `issuer_badgeclass`.`archived`,
       `issuer_badgeclass`.`badge_class_type`,
       `issuer_badgeinstance`.`issuer_id`,
       `issuer_badgeinstance`.`revoked`,
       `issuer_issuer`.`name_dutch`,
       `issuer_issuer`.`name_english`,
       `issuer_issuer`.`faculty_id`,
       `institution_faculty`.`name_dutch`,
       `institution_faculty`.`name_english`,
       `institution_faculty`.`faculty_type`,
       `institution_institution`.`institution_type`,
       EXTRACT(YEAR FROM CONVERT_TZ(`issuer_badgeinstance`.`created_at`, 'UTC', 'Europe/Amsterdam'))         AS `year`,
       EXTRACT(MONTH FROM CONVERT_TZ(`issuer_badgeinstance`.`created_at`, 'UTC', 'Europe/Amsterdam'))        AS `month`,
       COUNT(EXTRACT(MONTH FROM CONVERT_TZ(`issuer_badgeinstance`.`created_at`, 'UTC', 'Europe/Amsterdam'))) AS `nbr`
FROM `issuer_badgeinstance`
         INNER JOIN `issuer_badgeclass` ON (`issuer_badgeinstance`.`badgeclass_id` = `issuer_badgeclass`.`id`)
         INNER JOIN `issuer_issuer` ON (`issuer_badgeinstance`.`issuer_id` = `issuer_issuer`.`id`)
         INNER JOIN `institution_faculty` ON (`issuer_issuer`.`faculty_id` = `institution_faculty`.`id`)
         INNER JOIN `institution_institution`
                    ON (`institution_faculty`.`institution_id` = `institution_institution`.`id`)
WHERE (NOT (`issuer_badgeinstance`.`expires_at` <= '2025-05-21 06:08:20.902629' AND
            `issuer_badgeinstance`.`expires_at` IS NOT NULL) AND
       `issuer_badgeinstance`.`created_at` >= '2023-01-01 23:00:00' AND
       `issuer_badgeinstance`.`created_at` < '2023-12-31 23:00:00' AND NOT (`institution_faculty`.`institution_id` = 1))
GROUP BY `issuer_badgeinstance`.`award_type`, `issuer_badgeinstance`.`badgeclass_id`, `issuer_badgeclass`.`name`,
         `issuer_badgeclass`.`archived`, `issuer_badgeclass`.`badge_class_type`, `issuer_badgeinstance`.`issuer_id`,
         `issuer_badgeinstance`.`revoked`, `issuer_issuer`.`name_dutch`,
         `issuer_issuer`.`name_english`, `issuer_issuer`.`faculty_id`, `institution_faculty`.`name_english`,
         `institution_faculty`.`name_dutch`, `institution_faculty`.`faculty_type`,
         `institution_institution`.`institution_type`, 16, 17
ORDER BY 16 ASC, 17 ASC;
args=('UTC', 'Europe/Amsterdam', 'UTC', 'Europe/Amsterdam', 'UTC', 'Europe/Amsterdam', '2025-05-21 06:08:20.902629', '2023-01-01 23:00:00', '2023-12-31 23:00:00', 1);