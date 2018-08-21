
FROM ubuntu

RUN mkdir /certbot
RUN mkdir /certbot/certs
COPY . /certbot
WORKDIR /certbot
RUN chmod 775 dehydrated.sh
RUN apt update && apt install -y openssl curl python-pip python-dev build-essential
RUN pip install f5-sdk
RUN ["/bin/sh", "certbot_auto.sh"]


