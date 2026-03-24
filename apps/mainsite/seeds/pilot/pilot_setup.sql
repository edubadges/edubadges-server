-- Note: This file contains only the 6 requested institutions:
-- 1. SURFnet (ID: 2)
-- 2. SURF (ID: 3)
-- 3. University of Groningen (RUG) (ID: 22)
-- 4. Delft University of Technology (TU Delft) (ID: 33)
-- 5. HAN University of Applied Sciences (ID: 17)
-- 6. Fontys University of Applied Sciences (ID: 9)

INSERT INTO "oauth2_provider_application" VALUES
(1, 'public', '', 'public', 'password', 'unused', '', NULL, false, '2020-09-23 15:25:19.423578', '2020-09-23 15:25:19.423578', '');

INSERT INTO "mainsite_applicationinfo" VALUES
(1, NULL, NULL, 1, '', NULL, false);

INSERT INTO "mainsite_badgrapp" VALUES
(1,true,'2020-07-22 13:22:37.804587','2020-10-01 15:05:45.369314','https://pilots.edubadges.nl', 'https://pilots.edubadges.nl/login/', 'https://pilots.edubadges.nl/change-password/', NULL, NULL, 'Edubadges', 'https://pilots.edubadges.nl/signup/', 'https://pilots.edubadges.nl/auth/login/', 'https://pilots.edubadges.nl/signup/success/', 'https://pilots.edubadges.nl/profile/', 'https://pilots.edubadges.nl/public/', 'https://pilots.edubadges.nl/oauth/', false, NULL, false);

--
-- Dumping data for table "institution_institution"
--

INSERT INTO "institution_institution" VALUES 
-- SURFnet (ID: 2)
(2,'SURFnet','aDYXgNnsT-WXxro8vfykSg','2020-09-23 14:16:44.380748','2024-11-13 14:00:06.172579',NULL,NULL,'0000','https://www.surf.nl/','uploads/institution/35d54c37-8b78-491a-8948-33ee9b36e2ce.png','surfnet.nl','uitvoering_overeenkomst','uitvoering_overeenkomst','In SURF, education and research institutions work together on ICT facilities and innovation in order to make full use of the opportunities offered by digitisation. In this way, together we can make better and more flexible education and research possible.','In SURF, education and research institutions work together on ICT facilities and innovation in order to make full use of the opportunities offered by digitisation. In this way, together we can make better and more flexible education and research possible.',NULL,'en_EN','','SURFnet',false,false,true,false,'surfnet.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)',NULL,NULL,NULL,false,false,false,'NL',true,'support@edubadges.nl'),

-- SURF (ID: 3)
(3,'SURF','y2C_ap_gTPm_dQaAE2Q-ww','2020-10-01 18:53:17.362562','2026-02-23 10:23:05.757393',NULL,NULL,'0000','https://www.surf.nl/','uploads/institution/surf-logo.png','surf.nl','uitvoering_overeenkomst','uitvoering_overeenkomst','In SURF, education and research institutions work together on ICT facilities and innovation in order to make full use of the opportunities offered by digitisation. In this way, together we can make better and more flexible education and research possible..','In SURF werken onderwijs- en onderzoeksinstellingen samen aan ICT-voorzieningen en innovatie om de mogelijkheden van digitalisering optimaal te benutten. Zo maken we samen beter en flexibeler onderwijs en onderzoek mogelijk.','SURF','en_EN','uploads/institution/e0ae6a48-5607-4c3e-9551-49270d8cf0a5.png','SURF',true,true,true,false,'surf.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)','206815',NULL,NULL,false,false,true,'NL',true,'support@edubadges.nl'),

-- University of Groningen (RUG) (ID: 22)
(22,'University of Groningen','_yF-0DaoTFKejs5ovFl5SQ','2021-09-27 09:33:37.244741','2024-11-13 14:00:06.191097',NULL,NULL,'21PC',NULL,'','rug.nl','gerechtvaardigd_belang','gerechtvaardigd_belang','','','WO','en_EN','','Rijksuniversiteit Groningen',true,true,true,false,'rug.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)','165742',NULL,NULL,false,false,true,'NL',true,'support@edubadges.nl'),

-- Delft University of Technology (TU Delft) (ID: 33)
(33,'Delft University of Technology','pGMO1rZiQK6ikuY4GDPHng','2022-05-04 08:39:12.573430','2024-11-13 14:00:06.199489',NULL,NULL,'21PF','https://d1rkab7tlqy5f1.cloudfront.net/TUDelft/Onderwijs/Opleidingen/Exchange/TU%20Delft%20grading%20scale%20January%202019%20MSc%20students.pdf','uploads/institution/be9d4543-7312-4b01-9a7a-254fa0bfe8e3.png','tudelft.nl','gerechtvaardigd_belang','gerechtvaardigd_belang','Delft University of Technology (Dutch: Technische Universiteit Delft), also known as TU Delft, is the oldest and largest Dutch public technical university, located in Delft, Netherlands.','TU Delft (Technische Universiteit Delft) is de oudste en grootste publieke universiteit in Nederland. De universiteit is opgericht op 8 januari 1842 in Delft.','WO','en_EN','uploads/institution/1f1078d6-75ec-439d-80a7-b093c4847bb0.png','TU Delft',true,true,true,false,'tudelft.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)','166529',NULL,NULL,false,false,true,'NL',true,'support@edubadges.nl'),

-- HAN University of Applied Sciences (ID: 17)
(17,'HAN University of Applied Sciences','BfCsJHbLR2uBwkK4EgfrDg','2021-04-22 13:30:56.181909','2025-03-26 16:07:12.692152',NULL,NULL,'25KB','https://hanuniversity.com/en/study-and-living/studying-at-han/dutch-education-system/','','han.nl','gerechtvaardigd_belang','gerechtvaardigd_belang','OPEN UP NEW HORIZONS','OPEN UP NEW HORIZONS','HBO','nl_NL','uploads/institution/d5a4831d-58da-4521-9eda-913671c848fd.png','Hogeschool van Arnhem en Nijmegen',true,true,true,false,'han.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)','12219',NULL,NULL,false,false,true,'NL',true,'support@edubadges.nl'),

-- Fontys University of Applied Sciences (ID: 9)
(9,'Fontys University of Applied Sciences','KhaNZNZgQp2vzFcjUP3Myg','2021-02-08 08:49:43.306467','2024-11-13 14:00:06.179001',NULL,NULL,'30GB','https://www.fontys.nl','uploads/institution/ab8dbd9c-210d-4d8e-a1b3-38033709261c.png','fontys.nl','gerechtvaardigd_belang','uitvoering_overeenkomst','Fontys is a future-forward University of Applied Sciences in the Netherlands, offering Bachelor and Master degree programmes and exchange tracks in various fields. The knowledge institute in technology, entrepreneurship and creativity.','Fontys is een toekomstgerichte hogeschool in Nederland met een breed aanbod bachelor- en masterstudies en uitwisselingsprogramma’s in verschillende vakgebieden. Hét kennisinstituut voor techniek, ondernemerschap en creativiteit.','HBO','en_EN','','Fontys University of Applied Sciences',true,true,true,false,'fontys.nl.tempguestidp.edubadges.nl','(.*@*.nl|.*@*.edu|.*@*.com)','8694',NULL,NULL,false,false,true,'NL',true,'support@edubadges.nl');

--
-- Dumping data for table "badgeuser_terms"
--

INSERT INTO "badgeuser_terms" VALUES 
(1,'2020-09-23 14:16:44.393802','2020-09-23 15:37:54.462266','issYapevSqq_gYFPm-bfpQ',1,'formal_badge',NULL,2,NULL),
(2,'2020-09-23 14:16:44.395828','2020-09-23 15:39:08.757372','RxWIunwdS8GXV8Ks0GzPUg',1,'informal_badge',NULL,2,NULL),
(6,'2020-10-01 18:54:04.966787','2025-01-28 16:59:56.081743','bo0Krj1tT0il5Tz-GzUd2g',2,'formal_badge',NULL,3,NULL),
(7,'2020-10-01 18:54:04.968194','2025-01-28 16:55:03.144144','1GsMfFqaREmu7kBhVnSDPw',2,'informal_badge',NULL,3,NULL),
(25,'2021-02-08 08:49:43.313825','2021-02-08 08:49:43.313884','6f1aWafeRhe6NqU5-cHDVw',1,'formal_badge',NULL,9,NULL),
(26,'2021-02-08 08:49:43.315669','2021-02-08 08:49:43.315705','vgWY2ku6RGWIU-6CFwxS1g',1,'informal_badge',NULL,9,NULL),
(38,'2021-04-22 13:30:56.187731','2021-04-22 13:30:56.187761','VuMfSnBlRcyY1FyvWhftbw',1,'informal_badge',NULL,17,NULL),
(46,'2021-09-27 09:33:37.253951','2021-09-27 09:54:37.966992','udweAhNPRkWojxT57UsK_g',1,'formal_badge',NULL,22,NULL),
(65,'2022-05-04 08:39:12.583224','2022-05-04 08:39:12.583263','4MlChxjDQLeImSS6YB5vOQ',1,'formal_badge',NULL,33,NULL),
(66,'2022-05-04 08:39:12.584712','2022-05-04 08:39:12.584745','gfUjC2Y5Tv6WgDk1KCClJw',1,'informal_badge',NULL,33,NULL),
(71,'2022-06-01 11:32:03.294884','2022-06-01 11:32:03.294943','cEmKcXioRgG81DXONoRN7w',1,'formal_badge',NULL,17,NULL),
(75,'2022-07-04 07:15:50.803720','2022-07-04 07:18:13.021087','jML7X0GTTdWltv5JqhYOmg',1,'informal_badge',NULL,22,NULL);

--
-- Dumping data for table "badgeuser_termsurl"
--

INSERT INTO "badgeuser_termsurl" VALUES
(7,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/formal-edubadges-agreement-en.md','en',1,false),
(8,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/formal-edubadges-agreement-nl.md','nl',1,false),
(9,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/formal-edubadges-agreement-en.md','en',1,true),
(10,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/formal-edubadges-agreement-nl.md','en',1,true),
(11,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/informal-edubadges-agreement-en.md','en',2,false),
(12,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/informal-edubadges-agreement-nl.md','nl',2,false),
(13,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/informal-edubadges-agreement-en.md','en',2,true),
(14,'https://raw.githubusercontent.com/edubadges/privacy/master/surfnet.nl/informal-edubadges-agreement-nl.md','nl',2,true),
(15,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/formal-edubadges-agreement-en.md','en',6,false),
(16,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/formal-edubadges-agreement-nl.md','nl',6,false),
(17,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/informal-edubadges-agreement-en.md','en',7,false),
(18,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/informal-edubadges-agreement-nl.md','nl',7,false),
(19,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/formal-edubadges-excerpt-en.md','en',6,true),
(20,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/formal-edubadges-excerpt-nl.md','nl',6,true),
(21,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/informal-edubadges-excerpt-en.md','en',7,true),
(22,'https://raw.githubusercontent.com/edubadges/privacy/master/surf/informal-edubadges-excerpt-nl.md','nl',7,true),
(67,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-formal-text-en.md','en',25,false),
(68,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-formal-text-nl.md','nl',25,false),
(69,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-formal-excerpt-en.md','en',25,true),
(70,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-formal-excerpt-nl.md','nl',25,true),
(71,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-nonformal-text-en.md','en',26,false),
(72,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-nonformal-text-nl.md','nl',26,false),
(73,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-nonformal-excerpt-en.md','en',26,true),
(74,'https://raw.githubusercontent.com/edubadges/privacy/master/fontys-hogescholen/edubadges-nonformal-excerpt-nl.md','nl',26,true),
(119,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-nonformal-text-en.md','en',38,false),
(120,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-nonformal-text-nl.md','nl',38,false),
(121,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-nonformal-excerpt-en.md','en',38,true),
(122,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-nonformal-excerpt-nl.md','nl',38,true),
(151,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-formal-text-en.md','en',46,false),
(152,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-formal-text-nl.md','nl',46,false),
(153,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-formal-excerpt-en.md','en',46,true),
(154,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-formal-excerpt-nl.md','nl',46,true),
(227,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-formal-excerpt-en.md','en',65,true),
(228,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-formal-excerpt-nl.md','nl',65,true),
(229,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-formal-text-en.md','en',65,false),
(230,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-formal-text-nl.md','nl',65,false),
(231,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-nonformal-excerpt-en.md','en',66,true),
(232,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-nonformal-excerpt-nl.md','nl',66,true),
(233,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-nonformal-text-en.md','en',66,false),
(234,'https://raw.githubusercontent.com/edubadges/privacy/master/tu-delft/edubadges-nonformal-text-nl.md','nl',66,false),
(251,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-formal-excerpt-en.md','en',71,true),
(252,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-formal-excerpt-nl.md','nl',71,true),
(253,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-formal-text-en.md','en',71,false),
(254,'https://raw.githubusercontent.com/edubadges/privacy/master/han-university-of-applied-sciences/edubadges-formal-text-nl.md','nl',71,false),
(267,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-nonformal-excerpt-en.md','en',75,true),
(268,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-nonformal-excerpt-nl.md','nl',75,true),
(269,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-nonformal-text-en.md','en',75,false),
(270,'https://raw.githubusercontent.com/edubadges/privacy/master/rijksuniversiteit-groningen/edubadges-nonformal-text-nl.md','nl',75,false);

-- This file now contains the 6 requested institutions with their related badgeuser_terms and badgeuser_termsurl data:
-- 1. SURFnet (ID: 2) - 12 terms records
-- 2. SURF (ID: 3) - 12 terms records  
-- 3. University of Groningen (RUG) (ID: 22) - 7 terms records
-- 4. Delft University of Technology (TU Delft) (ID: 33) - 3 terms records
-- 5. HAN University of Applied Sciences (ID: 17) - 3 terms records
-- 6. Fontys University of Applied Sciences (ID: 9) - 10 terms records
-- Plus related badgeuser_termsurl records: 48 records
