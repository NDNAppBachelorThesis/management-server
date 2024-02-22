# This contains a management server for the NDN-IoT project

## Mirror

If you are viewing this from a mirror then please visit `https://github.com/NDNAppBachelorThesis/management-server` to
access the build artifacts

# Docker Image

The docker image serves this django project. It also ensures that the database
exists and an admin user get created. It defaults to username ``admin`` and password
``root``.

## Admin user

You probably want to change the credentials of the admin user. Do you by changing
the following ENV variables:

- ``DJANGO_SUPERUSER_USERNAME``
- ``DJANGO_SUPERUSER_EMAIL``
- ``DJANGO_SUPERUSER_PASSWORD``
