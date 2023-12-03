FROM python:3.9.6-slim

STOPSIGNAL SIGINT
EXPOSE 8080

ENV DJANGO_SUPERUSER_USERNAME=admin
ENV DJANGO_SUPERUSER_EMAIL=admin@example.com
ENV DJANGO_SUPERUSER_PASSWORD=root

WORKDIR "/server"

ADD requirements.txt /server
RUN python3 -m pip install -r requirements.txt
ADD . /server
ENV PYTHONPATH=$PYTHONPATH:/server

RUN python3 manage.py collectstatic

CMD ["sh", "-c", "python manage.py migrate && (python manage.py createsuperuser --no-input || true) && exec python manage.py runserver --noreload 0.0.0.0:8080"]
