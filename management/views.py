import json
import os
import re
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

from management.models import *


class NDNUtilMixin(LoginRequiredMixin):
    login_url = 'login'


class IndexView(NDNUtilMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        return {

        }


class LoginView(TemplateView):
    template_name = 'login.html'

    def post(self, request: WSGIRequest):
        path = request.GET.get('next') or reverse('index')
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember-me') == 'on'

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

    def get(self, request: WSGIRequest):
        logout(request)
        return redirect(reverse('login'))


class BoardsView(NDNUtilMixin, TemplateView):
    template_name = "boards.html"

    def get_context_data(self, **kwargs):
        boards = list(Boards.objects.all())
        boards.sort(key=lambda b: (b.active, b.id), reverse=True)

        return {
            'boards': boards,
        }


class UpdateView(NDNUtilMixin, TemplateView):
    template_name = "update.html"

    def get_context_data(self):
        boards = Boards.objects.filter(last_ping_time__gte=datetime.datetime.utcnow() - datetime.timedelta(seconds=5))

        return {
            'boards': boards,
        }


class FirmwareUpdateCompleteView(NDNUtilMixin, View):

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


@method_decorator(csrf_exempt, name='dispatch')
class RegisterBoard(View):

    def _get_nfd_container(self, docker_client: docker.DockerClient):
        containers = docker_client.containers.list()
        for container in containers:
            for tag in container.image.tags:
                if tag.startswith('derteufelqwe/ndn-nfd'):
                    return container

    def post(self, request: WSGIRequest):
        data = json.loads(request.body)
        deviceIp = data["ip"]
        deviceId = data["deviceId"]

        board = Boards.objects.get_or_create(device_id=data['deviceId'])[0]
        board.ip = deviceIp
        board.save()

        # Try register board at NFD
        try:
            if os.getenv("DEBUG") == "true":
                docker_client = docker.DockerClient(base_url='tcp://192.168.178.179:2375')
            else:
                docker_client = docker.DockerClient(base_url='unix://var/run/docker.sock')
            docker_client.ping()

            try:
                nfd_container = self._get_nfd_container(docker_client)
                cmd_result1 = nfd_container.exec_run(f'sh addNode.sh "{deviceIp}" "/esp/{deviceId}"')
                cmd_result2 = nfd_container.exec_run(f'sh addNode.sh "{deviceIp}" "/esp/discovery"')

                if cmd_result1.exit_code != 0:
                    print(f'Failed to add NFD route for {deviceId} ({deviceIp}).\n'
                          f'Exit code: {cmd_result1.exit_code}\n'
                          f'Output:\n '
                          f'{cmd_result1.output.decode()}')
                elif cmd_result2.exit_code != 0:
                    print(f'Failed to add NFD discovery route for {deviceId} ({deviceIp}).\n'
                          f'Exit code: {cmd_result2.exit_code}\n'
                          f'Output:\n '
                          f'{cmd_result2.output.decode()}')
                else:
                    print(f'Added NFD routes for {deviceId} ({deviceIp})')
            except Exception as e:
                print(f"Failed to register NFD route in docker. Exception: {e}")

        except Exception:
            print('Could not connect to docker daemon')


        return HttpResponse("OK")


@method_decorator(csrf_exempt, name='dispatch')
class PingView(View):

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

    def get(self, request):
        settings = Settings.get_instance()

        return JsonResponse({
            'ndfIp': settings.ndn_router_ip,
        })
