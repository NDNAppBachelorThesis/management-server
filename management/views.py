import datetime
import json

from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from management.models import *


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        return {

        }


class BoardsView(TemplateView):
    template_name = "boards.html"

    def get_context_data(self, **kwargs):
        boards = list(Boards.objects.all())
        boards.sort(key=lambda b: (b.active, b.id))

        return {
            'boards': boards,
        }


@method_decorator(csrf_exempt, name='dispatch')
class RegisterBoard(View):

    def post(self, request: WSGIRequest):
        data = json.loads(request.body)

        board = Boards.objects.get_or_create(device_id=data['deviceId'])[0]
        board.ip = data['ip']
        board.save()

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


class UpdateView(TemplateView):
    template_name = "update.html"

    def get_context_data(self):
        boards = Boards.objects.filter(last_ping_time__gte=datetime.datetime.utcnow() - datetime.timedelta(seconds=5))

        return {
            'boards': boards,
        }


class FirmwareUpdateCompleteView(View):

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
