FROM ubuntu:14.04
MAINTAINER Amara "http://amara.org"
ENV DEBIAN_FRONTEND noninteractive
RUN (echo "deb http://archive.ubuntu.com/ubuntu trusty main universe multiverse" > /etc/apt/sources.list)
RUN (echo "deb-src http://archive.ubuntu.com/ubuntu trusty main universe multiverse" >> /etc/apt/sources.list)
RUN (echo "deb http://archive.ubuntu.com/ubuntu trusty-updates main universe multiverse" >> /etc/apt/sources.list)
RUN (echo "deb-src http://archive.ubuntu.com/ubuntu trusty-updates main universe multiverse" >> /etc/apt/sources.list)
RUN locale-gen en_US.UTF-8
RUN apt-get update
RUN apt-get -y --force-yes install wget python-dev python-setuptools make gcc libmysqlclient-dev libmemcached-dev supervisor libxml2-dev libxslt-dev zlib1g-dev swig libffi-dev libssl-dev libyaml-dev git-core python-m2crypto subversion openjdk-6-jre libjpeg-dev libfreetype6-dev gettext build-essential gcc dialog mysql-client node-uglify ruby-sass libav-tools libz-dev
ENV APP_DIR /opt/apps/amara
ENV CLOSURE_PATH /opt/google-closure
RUN git clone https://github.com/google/closure-library $CLOSURE_PATH
RUN (cd $CLOSURE_PATH && git checkout adbcc8ef6530ea16bac9f877901fe6b32995c5ff)
RUN easy_install pip
# install urllib3[secure] before other packages.  This prevents SSL warnings
RUN pip install --upgrade urllib3[secure]
COPY deploy /tmp/deploy
RUN (cd /tmp/deploy && pip install --src /opt/src/amara/ -r requirements.txt)
RUN rm -fr /tmp/deploy
RUN mkdir -p /opt/extras/pictures
RUN mkdir -p /opt/extras/videos
# this fixes the nose bug (https://github.com/django-nose/django-nose/issues/54)
RUN rm /usr/local/man
RUN mkdir -p /var/run/amara
RUN useradd --home /var/run/amara --shell /bin/bash amara
RUN mkdir /var/run/amara/test-output/
RUN chown -R amara:amara /var/run/amara
WORKDIR /var/run/amara
EXPOSE 8000
ENV MANAGE_SCRIPT /opt/apps/amara/manage.py
ENV DJANGO_SETTINGS_MODULE unisubs_settings
ENV REVISION staging
ENTRYPOINT ["/usr/local/bin/entry"]
CMD ["app"]
COPY .docker/known_hosts /root/.ssh/known_hosts
COPY .docker/bin/* /usr/local/bin/
COPY . /opt/apps/amara
RUN ln -sf $CLOSURE_PATH $APP_DIR/media/js/closure-library
USER amara
