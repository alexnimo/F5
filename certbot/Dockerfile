FROM alpine

RUN mkdir /certbot
RUN mkdir /certbot/certs
COPY . /certbot
RUN ["/bin/bash", "certbot_auto.sh"]
