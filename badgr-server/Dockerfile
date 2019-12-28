FROM centos:7
LABEL image="badgr-server"
LABEL versie="0.1"
LABEL datum="2018 03 02"

RUN yum -y install epel-release git git-core mlocate
RUN yum -y install cairo
RUN yum -y install python-virtualenv gcc python-pip python-devel mysql-devel libjpeg-turbo libjpeg-turbo-devel zlib-devel openldap-devel cyrus-sasl-devel swig libxslt-devel automake autoconf libtool libffi-devel libyaml-devel libxml2 openssl-devel sudo curl wget supervisor

RUN yum -y install gcc-c++ patch readline readline-devel zlib zlib-devel libyaml-devel libffi-devel openssl-devel make bzip2 autoconf automake libtool bison iconv-devel which
RUN pip install --upgrade pip

# Set correct timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Amsterdam /etc/localtime

# setup webserver
RUN pip install gunicorn
RUN mkdir /var/log/gunicorn
RUN touch /var/log/gunicorn/error.log && \
    touch /var/log/gunicorn/access.log

# setup proxyserver
RUN yum -y update && \
    yum -y install epel-release &&\
    yum -y install nginx

ADD config/nginx/nginx.conf /etc/nginx/nginx.conf
ADD config/nginx/nginx_badgr.conf /etc/nginx/conf.d/nginx_badgr.conf
RUN touch /var/log/nginx/error.log && \
    touch /var/log/nginx/access.log

ADD badgr/badgr-server /var/badgr/code
ADD config/badgr/settings_local.py /var/badgr/code/apps/mainsite/settings_local.py

RUN mkdir /var/badgr/code/cert/
ADD config/nginx/certs/<YOURHOST>.pem /var/badgr/code/cert/<YOURHOST>.pem
ADD config/nginx/certs/<YOURHOST>.key /var/badgr/code/cert/<YOURHOST>.key

RUN cd /var/badgr/code && \
    pip install -r requirements.txt && \
    pip install -r apps/ims/requirements.txt

RUN cd /var/badgr/ && \
    virtualenv env && \
    source env/bin/activate

ADD entrypoint/supervisord.conf /etc/supervisord.conf
EXPOSE 80 443 5678
CMD ["/usr/bin/supervisord"]