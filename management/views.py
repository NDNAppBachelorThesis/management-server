import json
import os
import re
from typing import List

import requests

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import urlencode
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
import docker
from docker.models.containers import Container

from management.models import *


def get_docker_client():
    """
    Returns the docker client if possible
    """

    try:
        if os.getenv("DEBUG") == "true":
            docker_client = docker.DockerClient(base_url='tcp://192.168.178.179:2375')
        else:
            docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        docker_client.ping()
        return docker_client

    except Exception:
        print('Could not connect to docker daemon')

    return None


class NDNUtilMixin(LoginRequiredMixin):
    """
    A mixin, which configures the required login
    """

    login_url = 'login'


class IndexView(NDNUtilMixin, TemplateView):
    """
    The index page, which shows a nice overview
    """

    template_name = "index.html"

    def _get_service_container(self, containers: List[Container], label_name=None):
        """
        Filters all available containers for a given label
        """

        for container in containers:
            if container.labels.get('de.matthes.ndn_app') == label_name:
                return container

    def get_context_data(self, **kwargs):
        mgmt_container = None
        nfd_container = None
        grafana_container = None
        crate_container = None
        mongo_container = None
        orion_container = None
        quantumleap_container = None
        link_quality_handler_container = None
        ndn_adapter_container = None

        all_operational = None

        # Try to get all relevant containers
        if docker_client := get_docker_client():
            containers = docker_client.containers.list()
            mgmt_container = self._get_service_container(containers, 'management')
            nfd_container = self._get_service_container(containers, 'nfd')
            grafana_container = self._get_service_container(containers, 'grafana')
            crate_container = self._get_service_container(containers, 'crate')
            mongo_container = self._get_service_container(containers, 'mongo')
            orion_container = self._get_service_container(containers, "fiware-orion")
            quantumleap_container = self._get_service_container(containers, 'quantumleap')
            link_quality_handler_container = self._get_service_container(containers, 'ndn-link-quality-handler')
            ndn_adapter_container = self._get_service_container(containers, 'ndn-adapter')

            all_containers = [
                mgmt_container, nfd_container, grafana_container, crate_container, mongo_container, orion_container,
                quantumleap_container, link_quality_handler_container, ndn_adapter_container
            ]

            all_stati = ['offline' if c is None else c.status for c in all_containers]
            all_operational = all([s == 'running' for s in all_stati])

        all_boards = Boards.objects.all()

        return {
            'mgmt_container': mgmt_container,
            'nfd_container': nfd_container,
            'grafana_container': grafana_container,
            'crate_container': crate_container,
            'mongo_container': mongo_container,
            'orion_container': orion_container,
            'quantumleap_container': quantumleap_container,
            'link_quality_handler_container': link_quality_handler_container,
            'ndn_adapter_container': ndn_adapter_container,
            'all_operational': all_operational,
            'boards_cnt': all_boards.count(),
            'active_boards_cnt': sum([1 for b in all_boards if b.active]),
            'nfd_ip': Settings.objects.first().ndn_router_ip if Settings.objects.first() else '<Empty>'
        }


class LoginView(TemplateView):
    """
    The login page
    """

    template_name = 'login.html'

    def post(self, request: WSGIRequest):
        path = request.GET.get('next') or reverse('index')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(path)

        res = redirect('login')
        res['Location'] += '?' + urlencode({'next': path, 'error': 'true'})
        return res

    def get_context_data(self, **kwargs):
        return {}


class LogoutView(NDNUtilMixin, View):
    """
    Invalidates the current session and redirects to the login page
    """

    def get(self, request: WSGIRequest):
        logout(request)
        return redirect(reverse('login'))


class BoardsView(NDNUtilMixin, TemplateView):
    """
    Lists all boards and their infos
    """

    template_name = "boards.html"

    def get_context_data(self, **kwargs):
        boards = list(Boards.objects.all())
        boards.sort(key=lambda b: (b.active, b.id), reverse=True)

        return {
            'boards': boards,
        }


class UpdateView(NDNUtilMixin, TemplateView):
    """
    The view for OTA updates.
    Note: The actual updating is done from the clients browser. This view has nothing to do with it
    """
    template_name = "update.html"

    def get_context_data(self):
        boards = Boards.objects.filter(last_ping_time__gte=datetime.datetime.utcnow() - datetime.timedelta(seconds=5))

        return {
            'boards': boards,
        }


class FirmwareUpdateCompleteView(NDNUtilMixin, View):
    """
    Used by the UpdateView to notify the server when an OTA update finished
    """

    def post(self, request, board_id: int):

        try:
            board = Boards.objects.get(id=board_id)
        except Boards.DoesNotExist:
            return HttpResponse("BOARD_NOT_EXIST", status=400)

        successful = request.POST.get('success') in ('True', 'true', 1)

        board.last_flash_time = datetime.datetime.utcnow()
        board.last_flash_successful = successful
        board.save()

        return HttpResponse("OK")


class SettingsView(NDNUtilMixin, TemplateView):
    """
    The view to modify the settings.
    Currently only the NFD IP is a setting.
    """

    template_name = 'settings.html'

    def post(self, request):
        post_ndn_ip = request.POST.get('ndnIp')
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', post_ndn_ip):
            return redirect('settings')

        settings = Settings.get_instance()
        settings.ndn_router_ip = post_ndn_ip
        settings.save()

        return redirect('settings')

    def get_context_data(self):
        return {
            'settings': Settings.get_instance(),
        }


class LogsView(NDNUtilMixin, TemplateView):
    """
    View, which displays the logs of an ESP32 to the user.
    The logs are just grabbed from the devices HTTP log page
    """

    template_name = 'logs.html'

    def get_context_data(self, board_id: int):
        board = Boards.objects.get(id=board_id)

        log_text = 'Device is offline'
        if board.active:
            try:
                r = requests.get(f'http://{board.ip}/log', timeout=3)
                log_text = r.text
            except Exception:
                log_text = 'Could not connect to device.'

        return {
            'board': board,
            'log': log_text,
        }


# -----  API views  -----

# CSRF must be disabled for all APIs
@method_decorator(csrf_exempt, name='dispatch')
class RegisterBoard(View):
    """
    Registers a board
    """

    def _get_nfd_container(self, docker_client: docker.DockerClient):
        """
        Filters all available containers for the NFD container
        """

        containers = docker_client.containers.list()
        for container in containers:
            if container.labels.get('de.matthes.ndn_app') == 'nfd':
                return container

    def post(self, request: WSGIRequest):
        data = json.loads(request.body)
        device_ip = data["ip"]
        device_id = data["deviceId"]

        board = Boards.objects.get_or_create(device_id=device_id)[0]
        board.ip = device_ip
        board.save()

        # Try register board at NFD
        if docker_client := get_docker_client():
            try:
                nfd_container = self._get_nfd_container(docker_client)
                cmd_result1 = nfd_container.exec_run(f'sh addNode.sh "{device_ip}" "/esp/{device_id}"')
                cmd_result2 = nfd_container.exec_run(f'sh addNode.sh "{device_ip}" "/esp/discovery"')
                cmd_result3 = nfd_container.exec_run(f'sh addNode.sh "{device_ip}" "/esp/linkqualitycheck"')

                if cmd_result1.exit_code != 0:
                    print(f'Failed to add NFD route for {device_id} ({device_ip}).\n'
                          f'Exit code: {cmd_result1.exit_code}\n'
                          f'Output:\n '
                          f'{cmd_result1.output.decode()}')
                elif cmd_result2.exit_code != 0:
                    print(f'Failed to add NFD discovery route for {device_id} ({device_ip}).\n'
                          f'Exit code: {cmd_result2.exit_code}\n'
                          f'Output:\n '
                          f'{cmd_result2.output.decode()}')
                elif cmd_result3.exit_code != 0:
                    print(f'Failed to add NFD discovery route for {device_id} ({device_ip}).\n'
                          f'Exit code: {cmd_result3.exit_code}\n'
                          f'Output:\n '
                          f'{cmd_result3.output.decode()}')
                else:
                    print(f'Added NFD routes for {device_id} ({device_ip})')
            except Exception as e:
                print(f"Failed to register NFD route in docker. Exception: {e}")

        return HttpResponse("OK")


@method_decorator(csrf_exempt, name='dispatch')
class PingView(View):
    """
    View for the ESP32 boards to ping to
    """

    def post(self, request, device_id: int):

        try:
            board = Boards.objects.get(device_id=device_id)
        except Boards.DoesNotExist:
            return HttpResponse("BOARD_NOT_EXIST", status=400)

        board.last_ping_time = datetime.datetime.utcnow()
        board.save()

        return HttpResponse("PONG")


@method_decorator(csrf_exempt, name='dispatch')
class SettingsApiView(View):
    """
    View for the ESP32 boards to request the NFD IP from
    """

    def get(self, request):
        settings = Settings.get_instance()

        return JsonResponse({
            'ndfIp': settings.ndn_router_ip,
        })
