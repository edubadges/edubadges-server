CREATE database badgr;
SET GLOBAL sql_mode='';
GRANT ALL on *.* to 'badgr'@'localhost' identified by 'secret';
flush privileges;