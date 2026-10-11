"""Component-level tests: key states render, and the honesty / accessibility rules hold."""
import re
from datetime import timedelta

from django.template.loader import render_to_string
from django.test import SimpleTestCase, TestCase
from django.utils import timezone


class ComponentStates(SimpleTestCase):
    def test_action_badge_has_icon_and_label_not_just_colour(self):
        for action, label in [("IRRIGATE_NOW", "Water now"), ("IRRIGATE_LATER_TODAY", "Water later today"), ("SKIP_TODAY", "Skip today"), ("WATCH", "Watch closely")]:
            html = render_to_string("components/action_badge.html", {"action": action, "lang": "en"})
            self.assertIn(label, html)
            self.assertIn("<svg", html)

    def test_action_badge_pidgin(self):
        self.assertIn("No water am today", render_to_string("components/action_badge.html", {"action": "SKIP_TODAY", "lang": "pcm"}))

    def test_confidence_meter_levels(self):
        for level, filled in (("High", 3), ("Medium", 2), ("Low", 1)):
            html = render_to_string("components/confidence_meter.html", {"level": level})
            self.assertEqual(len(re.findall(r"x-grow", html)), filled, level)
            self.assertIn(f"{level} confidence", html)

    def test_stale_freshness_pill_says_out_of_date(self):
        old = timezone.now() - timedelta(hours=9)
        stale = render_to_string("components/data_freshness.html", {"time": old, "stale": True, "label": "Forecast"})
        fresh = render_to_string("components/data_freshness.html", {"time": timezone.now(), "stale": False, "label": "Forecast"})
        self.assertIn("out of date", stale)
        self.assertNotIn("out of date", fresh)

    def test_demo_badge_label(self):
        self.assertIn("Demo data", render_to_string("components/demo_badge.html"))
        self.assertIn("Simulated satellite", render_to_string("components/demo_badge.html", {"label": "Simulated satellite"}))

    def test_rain_dial_prints_the_number(self):
        html = render_to_string("components/rain_dial.html", {"prob": 60, "uid": 1, "size": 56})
        self.assertIn("60%", html)
        self.assertIn('aria-label="60 percent chance of rain"', html)

    def test_signal_bar_has_text_alternative(self):
        s = {"label": "Soil moisture", "display": "19%", "status": "stress", "share": 0.5, "direction": "irrigate"}
        html = render_to_string("components/signal_bar.html", {"s": s, "delay": 0})
        self.assertIn("Pushes toward watering", html)
        self.assertIn("50%", html)

    def test_empty_state_has_one_next_step(self):
        html = render_to_string("components/empty_state.html", {"title": "No fields yet", "text": "Add one.", "href": "/farms/onboarding/", "cta": "Add a field"})
        self.assertEqual(html.count("<a "), 1)

    def test_css_has_reduced_motion_fallback_and_focus_ring(self):
        from pathlib import Path

        css = (Path(__file__).resolve().parents[2] / "static" / "src" / "input.css").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn(":focus-visible", css)


class PageA11y(TestCase):
    def test_login_page_basics(self):
        html = self.client.get("/accounts/login/").content.decode()
        self.assertIn('<html lang="en"', html)
        self.assertRegex(html, r'<label class="label" for="identifier"')
        self.assertIn('id="main"', html)
        self.assertIn("Skip to content", html)

    def test_all_images_and_svgs_are_hidden_or_labelled(self):
        html = self.client.get("/design/").content.decode()
        for svg in re.findall(r"<svg[^>]*>", html):
            if "<use" in svg:
                continue
            self.assertTrue("aria-hidden" in svg or "role=" in svg or "aria-label" in svg or 'style="position:absolute' in svg, svg)
