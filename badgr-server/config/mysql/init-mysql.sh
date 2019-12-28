#!/bin/bash -v
/usr/bin/mysqladmin -u root password 'mysqlPassword'
mysql -uroot -pmysqlPassword -e "CREATE DATABASE badgr"
mysql -uroot -pmysqlPassword -e "GRANT ALL PRIVILEGES ON badgr.* TO 'badgr_user'@'localhost' IDENTIFIED BY 'secret'; FLUSH PRIVILEGES;"
mysql -uroot -pmysqlPassword -e "GRANT ALL PRIVILEGES ON *.* TO 'badgr_user'@'%' IDENTIFIED BY 'secret' WITH GRANT OPTION; FLUSH PRIVILEGES;"
mysql -uroot -pmysqlPassword -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' IDENTIFIED BY 'secret' WITH GRANT OPTION; FLUSH PRIVILEGES;"
mysql -uroot -pmysqlPassword -e "select user, host FROM mysql.user;"