from django.core.management.base import BaseCommand

from apps.demo import services


class Command(BaseCommand):
    help = "Create demo users and a realistic Calabar South farm with 90 days of history (all labelled Demo data)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Rebuild the demo farm from scratch")

    def handle(self, *args, **opts):
        farmer, partner, admin, _ = services._users()
        if opts["reset"] or not farmer.farms.filter(is_demo=True).exists():
            services.seed_farm(farmer)
        self.stdout.write(self.style.SUCCESS(
            f"Demo ready.\n  Farmer:  {services.DEMO_EMAIL}\n  Partner: {services.PARTNER_EMAIL}\n  Admin:   {services.ADMIN_EMAIL}\n  Password: {services.DEMO_PASSWORD}\n  Pilot code: CALABAR2026"))
