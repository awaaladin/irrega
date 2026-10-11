from datetime import date, timedelta

from django.test import SimpleTestCase

from .core import DayWeather, EngineInput, recommend

TODAY = date(2026, 7, 10)
MAIZE = [["initial", 20, 0.30], ["development", 35, 0.80], ["mid", 40, 1.20], ["late", 30, 0.60]]
LOAM = {"fc": 30, "wp": 12, "sat": 38}


def make(**kw):
    base = dict(
        today=TODAY, planting_date=TODAY - timedelta(days=70), stages=MAIZE, root_depth_mm=700, p=0.55,
        sensitive_stage="mid", soil=LOAM, area_m2=1000, efficiency=0.7, method="manual",
        moisture=24.0, moisture_age_h=2, forecast=[DayWeather(TODAY, 0, 5, 4.5, 30, 23), DayWeather(TODAY + timedelta(1), 0, 5, 4.5, 30, 23)],
        weather_age_h=1, ndvi=[(TODAY - timedelta(days=d), 0.72) for d in (15, 10, 5, 0)],
    )
    base.update(kw)
    return EngineInput(**base)


def rain(mm, prob, et0=3.5):
    return [DayWeather(TODAY, mm, prob, et0, 27, 22), DayWeather(TODAY + timedelta(1), mm, prob, et0, 27, 22)]


class EngineTests(SimpleTestCase):
    def test_heavy_rain_forecast_skips(self):
        out = recommend(make(moisture=23.0, forecast=rain(30, 90)))
        self.assertEqual(out["action"], "SKIP_TODAY")
        self.assertEqual(out["volume_l"], 0)
        self.assertIn(out["reasons"][0]["code"], ("RAIN_COVERS", "HEAVY_RAIN_SKIP"))

    def test_dry_hot_spell_at_flowering_irrigates(self):
        hot = [DayWeather(TODAY, 0, 5, 6.5, 35, 25), DayWeather(TODAY + timedelta(1), 0, 5, 6.5, 35, 25)]
        out = recommend(make(moisture=17.0, forecast=hot))
        self.assertEqual(out["action"], "IRRIGATE_NOW")
        self.assertTrue(out["stage"]["sensitive"])
        self.assertGreater(out["volume_l"], 0)
        self.assertTrue(out["window"])
        codes = [r["code"] for r in out["reasons"]]
        self.assertIn("SOIL_DRY", codes)
        self.assertIn("HOT_DEMAND", codes)

    def test_waterlogged_soil_with_falling_ndvi_watches_not_irrigates(self):
        falling = [(TODAY - timedelta(days=d), v) for d, v in ((15, 0.75), (10, 0.74), (5, 0.70), (0, 0.55))]
        out = recommend(make(moisture=39.0, ndvi=falling))
        self.assertEqual(out["action"], "WATCH")
        self.assertEqual(out["volume_l"], 0)
        self.assertEqual(out["reasons"][0]["code"], "NDVI_FALL_WET")

    def test_falling_ndvi_with_dry_soil_raises_urgency(self):
        falling = [(TODAY - timedelta(days=d), v) for d, v in ((15, 0.75), (10, 0.74), (5, 0.70), (0, 0.55))]
        base = make(moisture=23.0)
        with_ndvi = recommend(make(moisture=23.0, ndvi=falling))
        self.assertEqual(recommend(base)["action"], "SKIP_TODAY")
        self.assertTrue(with_ndvi["action"].startswith("IRRIGATE"))

    def test_missing_data_lowers_confidence(self):
        out = recommend(make(moisture=None, moisture_age_h=None, ndvi=[]))
        self.assertEqual(out["confidence"], "Low")
        self.assertIn("No soil moisture reading", out["confidence_notes"])
        self.assertTrue(any(r["code"] == "NO_MOISTURE" for r in out["reasons"]))

    def test_no_data_at_all_is_watch(self):
        out = recommend(make(moisture=None, moisture_age_h=None, forecast=[], weather_age_h=None, ndvi=[]))
        self.assertEqual(out["action"], "WATCH")
        self.assertEqual(out["confidence"], "Low")

    def test_stale_weather_flagged_and_lowers_confidence(self):
        fresh = recommend(make())
        stale = recommend(make(weather_age_h=30))
        self.assertTrue(any(r["code"] == "STALE_WEATHER" for r in stale["reasons"]))
        self.assertLess(stale["confidence_score"], fresh["confidence_score"])
        self.assertEqual(fresh["confidence"], "High")

    def test_yield_history_makes_trigger_slightly_earlier(self):
        hist = [{"amount_kg": 600, "dry_spell": True}, {"amount_kg": 900, "dry_spell": False}]
        a = recommend(make())["balance"]["raw_mm"]
        b = recommend(make(yields=hist))["balance"]["raw_mm"]
        self.assertLess(b, a)

    def test_signal_shares_sum_to_one(self):
        out = recommend(make(moisture=18.0))
        self.assertAlmostEqual(sum(s["share"] for s in out["signals"]), 1.0, places=1)

    def test_what_if_wait_when_irrigating(self):
        out = recommend(make(moisture=15.0, forecast=[DayWeather(TODAY, 0, 0, 6, 34, 25), DayWeather(TODAY + timedelta(1), 0, 0, 6, 34, 25)]))
        self.assertTrue(out["action"].startswith("IRRIGATE"))
        self.assertIn(out["what_if"]["risk"], ("medium", "high"))

    def test_human_units_for_manual_watering(self):
        out = recommend(make(area_m2=5, moisture=15.0))
        self.assertIn("watering cans", out["volume_human"])
        drip = recommend(make(area_m2=5, moisture=15.0, method="drip", efficiency=0.9))
        self.assertIn("litres", drip["volume_human"])
