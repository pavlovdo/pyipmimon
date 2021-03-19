FROM centos:latest
LABEL maintainer="Denis O. Pavlov pavlovdo@gmail.com"

ARG project

RUN   dnf update -y && \
    dnf install -y \
    bash-completion \
    cronie \
    epel-release \
    python38 && \
    rm -rf /var/cache/dnf

COPY *.py requirements.txt /usr/local/orbit/${project}/
WORKDIR /usr/local/orbit/${project}

RUN pip3.8 install -r requirements.txt

ENV TZ=Europe/Moscow
RUN ln -fs /usr/share/zoneinfo/$TZ /etc/localtime

RUN echo "00 * * * *  /usr/local/orbit/${project}/ipmi_sensors_discovery.py 1> /proc/1/fd/1 2> /proc/1/fd/2" > /tmp/crontab && \
    echo "*/1 * * * *   /usr/local/orbit/${project}/ipmi_sensors_trappers.py 1> /proc/1/fd/1 2> /proc/1/fd/2" >> /tmp/crontab && \
    crontab /tmp/crontab && rm /tmp/crontab

CMD ["crond","-n"]