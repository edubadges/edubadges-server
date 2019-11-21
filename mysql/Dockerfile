FROM centos/mysql-57-centos7
LABEL image="mysql"
LABEL versie="0.1"
LABEL datum="2018 03 05"

# set backup time to 01:01
ENV CRON_TIME="01 1 * * *"

USER root
RUN yum install -y cronie gzip yum python-setuptools python-pip \
&& rm -rf /var/cache/yum/* \
&& mkdir /backup /var/log/backup /var/log/cron
RUN easy_install supervisor

# Set correct timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

COPY ["config/mysql/backup.sh", "config/mysql/restore.sh", "/"]

RUN chmod u+x /backup.sh /restore.sh \
&& touch /var/log/backup/mysql_backup.log /var/log/cron/error.log /var/log/cron/access.log  \
&& chown -R mysql:mysql /backup.sh /restore.sh /backup /var/log/cron /var/log/backup

RUN echo "mysql" > /etc/cron.allow
RUN echo "${CRON_TIME} root . /root/.profile;/backup.sh >> /var/log/mysql_backup.log 2>&1" > /etc/cron.d/db-backup
RUN chmod 0644 /etc/cron.d/db-backup

ADD entrypoint/supervisord.conf /etc/supervisord.conf

USER mysql
ADD config/mysql/healthcheck.sh /var/opt/

USER root
# insert script that lets docker-compose variables being used by root profile in docker containter
COPY config/mysql/set-env.sh /set-env.sh
RUN chmod u+x /set-env.sh

ENTRYPOINT ["/usr/bin/supervisord"]