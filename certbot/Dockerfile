FROM ubuntu

RUN mkdir /certbot
RUN mkdir /certbot/certs
COPY . /certbot
WORKDIR /certbot
RUN chmod 775 dehydrated.sh
RUN chmod 775 certbot_hook.py
RUN apt update && apt install -y openssl curl python-pip python-dev build-essential
RUN pip install f5-sdk