from django.apps import AppConfig
from django.db.models.signals import post_migrate


class BillingConfig(AppConfig):
    name = 'apps.billing'

    def ready(self):
        from .services import ensure_plans

        post_migrate.connect(ensure_plans, sender=self)
