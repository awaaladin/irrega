"""End-to-end happy path and security checks. Weather and satellite run in their offline/simulated modes."""
import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.accounts.models import ApiKey
from apps.decisions.models import Decision
from apps.farms.models import Crop, Farm, Field

User = get_user_model()


def offline_weather():
    """Open-Meteo unreachable -> the engine must still answer (stale/low confidence), never crash."""
    return mock.patch("apps.providers.weather._fetch_open_meteo", side_effect=OSError("offline"))


class HappyPath(TestCase):
    def test_register_add_field_recommend_override_ask(self):
        with offline_weather():
            r = self.client.post("/accounts/register/", {"name": "Efiok", "identifier": "efiok@example.com", "password": "correct-horse-9"})
            self.assertRedirects(r, "/farms/onboarding/")
            r = self.client.post("/farms/onboarding/", {"name": "Test farm", "latitude": "4.95", "longitude": "8.32"})
            farm = Farm.objects.get(name="Test farm")
            self.assertEqual(r.status_code, 302)

            planting = (timezone.localdate() - timedelta(days=60)).isoformat()
            r = self.client.post(f"/farms/{farm.pk}/fields/new/", {
                "name": "Maize A", "crop": Crop.objects.get(key="maize").pk, "area_ha": "0.05", "soil": "loam", "planting_date": planting, "method": "manual"})
            self.assertEqual(r.status_code, 302)
            field = Field.objects.get(name="Maize A")

            # soil reading through the session API
            r = self.client.post(f"/api/fields/{field.pk}/moisture/", json.dumps({"value": 15}), content_type="application/json")
            self.assertEqual(r.status_code, 200)

            page = self.client.get(f"/farms/fields/{field.pk}/")
            self.assertContains(page, "Why this?")
            rec = field.recommendations.first()
            self.assertTrue(rec.action.startswith("IRRIGATE"), rec.action)  # dry soil, no forecast: still advises water

            # override: farmer skips
            r = self.client.post("/api/decisions/", json.dumps({"recommendation": rec.pk, "kind": "override", "farmer_action": "SKIP", "reason": "rain_started"}),
                                 content_type="application/json")
            self.assertEqual(r.status_code, 200)
            self.assertEqual(Decision.objects.get().farmer_action, "SKIP")

            # ask a question: grounded, streamed
            r = self.client.post("/api/ask/", json.dumps({"field": field.pk, "question": "How much water if I only have 5 cans?"}), content_type="application/json")
            text = b"".join(r.streaming_content).decode()
            self.assertIn("cans", text)
            r = self.client.post("/api/ask/", json.dumps({"field": field.pk, "question": "What will cassava sell for in Lagos?"}), content_type="application/json")
            self.assertIn("do not have", b"".join(r.streaming_content).decode())


class Security(TestCase):
    def setUp(self):
        self.a = User.objects.create_user(username="a@x.test", email="a@x.test", password="pw-12345678")
        self.b = User.objects.create_user(username="b@x.test", email="b@x.test", password="pw-12345678")
        farm = Farm.objects.create(owner=self.a, name="A farm")
        self.field = Field.objects.create(farm=farm, name="A1", crop=Crop.objects.get(key="tomato"), planting_date=timezone.localdate() - timedelta(days=40))

    def test_user_cannot_see_or_write_other_users_field(self):
        self.client.force_login(self.b)
        self.assertEqual(self.client.get(f"/farms/fields/{self.field.pk}/").status_code, 404)
        r = self.client.post(f"/api/fields/{self.field.pk}/moisture/", json.dumps({"value": 20}), content_type="application/json")
        self.assertEqual(r.status_code, 404)
        r = self.client.post("/api/ask/", json.dumps({"field": self.field.pk, "question": "hi"}), content_type="application/json")
        self.assertEqual(r.status_code, 404)

    def test_sensor_endpoint_needs_key_and_validates(self):
        body = json.dumps({"field": self.field.pk, "value": 22.5})
        self.assertEqual(self.client.post("/api/readings/", body, content_type="application/json").status_code, 401)
        key = ApiKey.objects.create(user=self.a)
        with offline_weather():
            ok = self.client.post("/api/readings/", body, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {key.key}")
            self.assertEqual(ok.status_code, 201)
            bad = self.client.post("/api/readings/", json.dumps({"field": self.field.pk, "value": 999}), content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {key.key}")
            self.assertEqual(bad.status_code, 400)
        other = ApiKey.objects.create(user=self.b)
        r = self.client.post("/api/readings/", body, content_type="application/json", HTTP_AUTHORIZATION=f"Bearer {other.key}")
        self.assertEqual(r.status_code, 404)

    def test_decision_history_is_immutable(self):
        from apps.decisions.models import Recommendation

        rec = Recommendation.objects.create(field=self.field, date=timezone.localdate(), action="SKIP_TODAY", confidence="High", payload={})
        d = Decision.objects.create(recommendation=rec, user=self.a, kind="accept")
        d.note = "changed"
        with self.assertRaises(PermissionError):
            d.save()
        with self.assertRaises(PermissionError):
            d.delete()

    def test_passwords_are_hashed_and_login_works_with_phone(self):
        u = User.objects.create_user(username="0803", phone="+2348031112222", password="pw-12345678")
        self.assertNotIn("pw-12345678", u.password)
        self.assertTrue(self.client.login(username="+2348031112222", password="pw-12345678"))


class NewFarmerToday(TestCase):
    def test_today_stays_on_today_and_explains_next_step(self):
        u = User.objects.create_user(username="new@x.test", email="new@x.test", password="pw-12345678")
        self.client.force_login(u)
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)  # no redirect to another tab
        self.assertContains(r, "set up your first field")
        self.assertContains(r, "/farms/onboarding/")


class Landing(TestCase):
    def test_signed_out_visitor_sees_the_landing_page_not_a_redirect(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Every screen, explained")
        for title in ("Today: one decision for each field", "Why this? The reasons, in plain words", "Override and snooze", "Partner dashboard and System", "Account and display"):
            self.assertContains(r, title)
        self.assertEqual(self.client.get("/about/").status_code, 200)

    def test_every_toc_link_has_a_target(self):
        from apps.farms.landing_content import SCREENS, TOC

        ids = {s["id"] for s in SCREENS} | {"how", "decisions", "screens", "words", "honest"}
        self.assertEqual({i for i, _ in TOC} - ids, set())

    def test_signed_in_farmer_still_gets_today(self):
        u = User.objects.create_user(username="s@x.test", email="s@x.test", password="pw-12345678")
        self.client.force_login(u)
        self.assertContains(self.client.get("/"), "set up your first field")


class DemoIsSafe(TestCase):
    def test_demo_partner_never_sees_real_farms_and_admin_entry_is_not_a_superuser(self):
        from apps.demo import services
        from apps.partners.views import _org_farms

        farmer, partner, admin, org = services._users()
        real = User.objects.create_user(username="real@x.test", email="real@x.test", password="pw-12345678", organization=org)
        Farm.objects.create(owner=real, name="Real farm", organization=org)
        Farm.objects.create(owner=farmer, name="Demo farm", organization=org, is_demo=True)
        names = set(_org_farms(partner).values_list("name", flat=True))
        self.assertEqual(names, {"Demo farm"})

    @override_settings(DEBUG=False)
    def test_admin_demo_entry_is_closed_when_not_debugging(self):
        self.assertEqual(self.client.get("/demo/enter/admin/").status_code, 404)
