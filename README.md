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


# Getting started developing
To get started developing locally you have to perform the following steps
1. Clone this repo and create a virtual environment and install the dependencies
2. Create the database migrations with `python manage.py migrate`
3. Create a superuser with `python manage.py createsuperuser` (follow the prompt)
4. Execute the `manage.py` script with the arguments `runserver 3000`
5. If you want to debug your docker connection modify the debug IP in the `get_docker_client` function
in `views.py`