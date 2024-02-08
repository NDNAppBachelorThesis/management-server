FROM python:3.9.6-slim
LABEL org.opencontainers.image.source = "https://github.com/NDNAppBachelorThesis/management-server"

STOPSIGNAL SIGINT
EXPOSE 3000
EXPOSE 32200/udp

ENV HOST_IP=""
ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=root

WORKDIR "/server"

ADD requirements.txt /server
RUN python3 -m pip install -r requirements.txt
ADD . /server
ENV PYTHONPATH=$PYTHONPATH:/server

RUN python3 manage.py collectstatic

CMD ["bash", "docker/startup.sh"]
