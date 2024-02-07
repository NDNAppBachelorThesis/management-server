import datetime

from django.db import models


class Boards(models.Model):
    id                    = models.BigAutoField(primary_key=True)
    device_id             = models.IntegerField(null=False)
    name                  = models.TextField(null=True)
    ip                    = models.TextField(null=False, max_length=32)
    last_flash_time       = models.DateTimeField(null=True)
    last_flash_successful = models.BooleanField(null=False, default=True)
    last_ping_time        = models.DateTimeField(null=True)

    @property
    def active(self) -> bool:
        """ Returns True if the last ping was not too old """
        if self.last_ping_time is None:
            return False
        return (datetime.datetime.utcnow() - self.last_ping_time).seconds < 10

    def __repr__(self):
        return f'Board({self.id}, {self.name})'


class Settings(models.Model):
    id              = models.BigAutoField(primary_key=True)
    ndn_router_ip   = models.TextField(null=True, default='')

    @staticmethod
    def get_instance() -> 'Settings':
        return Settings.objects.get_or_create(id=1)[0]

    def __repr__(self):
        return f'Settings()'
