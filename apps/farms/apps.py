from django.apps import AppConfig
from django.db.models.signals import post_migrate


class FarmsConfig(AppConfig):
    name = 'apps.farms'

    def ready(self):
        from .crops import ensure_crops

        post_migrate.connect(ensure_crops, sender=self)
