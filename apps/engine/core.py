"""Transparent water-balance engine. Pure Python: no Django imports, so it is easy to test and to explain.

Daily balance per field:
    ETc            = ET0 x Kc(stage)
    effective rain = forecast probability x expected mm x 0.75
    depletion      = (field capacity - soil moisture) x root depth
    RAW            = p x TAW  (water the crop can use before it is stressed)
Irrigate when depletion reaches RAW today (now) or will by tonight (later today),
unless forecast rain covers it. NDVI and yield history adjust urgency in small, explained steps.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

ACTIONS = ("IRRIGATE_NOW", "IRRIGATE_LATER_TODAY", "SKIP_TODAY", "WATCH")
RAIN_DISCOUNT = 0.75
DEFAULT_ET0 = 4.5  # mm/day, used only when weather is missing (lowers confidence)
CAN_LITRES = 15
DRUM_LITRES = 200
MAX_EVENT_MM = 30  # a single watering deeper than this mostly runs off; split it across days


@dataclass
class DayWeather:
    date: date
    rain_mm: float = 0.0
    rain_prob: float = 0.0  # percent
    et0: float = DEFAULT_ET0
    tmax: float = 30.0
    tmin: float = 23.0


@dataclass
class EngineInput:
    today: date
    planting_date: date
    stages: list  # [[name, days, kc], ...]
    root_depth_mm: float
    p: float
    sensitive_stage: str
    soil: dict  # fc, wp, sat (volumetric %)
    area_m2: float
    efficiency: float
    method: str = "manual"
    moisture: Optional[float] = None
    moisture_age_h: Optional[float] = None
    moisture_simulated: bool = False
    forecast: list = field(default_factory=list)  # DayWeather, today first
    weather_age_h: Optional[float] = None
    weather_demo: bool = False
    ndvi: list = field(default_factory=list)  # [(date, value)] oldest first
    ndvi_simulated: bool = False
    yields: list = field(default_factory=list)  # newest first: {"amount_kg", "dry_spell"}
    hour: int = 6  # local hour, picks the watering window


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def stage_for(stages, days):
    d = max(days, 0)
    elapsed = 0
    for i, (name, length, kc) in enumerate(stages):
        if d < elapsed + length:
            nxt = stages[i + 1][0] if i + 1 < len(stages) else None
            return name, kc, d - elapsed, (elapsed + length) - d, nxt
        elapsed += length
    return stages[-1][0], stages[-1][2], d - elapsed, 0, None


def ndvi_trend(series):
    """Return (latest, delta, state) where state is falling | stable | rising | unknown."""
    if len(series) < 2:
        return (series[-1][1] if series else None), 0.0, "unknown"
    latest = series[-1][1]
    prior = [v for _, v in series[:-1]][-4:]
    delta = latest - sum(prior) / len(prior)
    state = "falling" if delta <= -0.05 else "rising" if delta >= 0.05 else "stable"
    return latest, delta, state


def effective_rain(day: Optional[DayWeather]):
    return 0.0 if day is None else (day.rain_prob / 100.0) * day.rain_mm * RAIN_DISCOUNT


def litres_for(mm, inp):
    return mm * inp.area_m2 / inp.efficiency


def human_volume(litres, method):
    if litres <= 0:
        return ""
    if method != "manual":
        return f"{round(litres):,} litres"
    cans = litres / CAN_LITRES
    if cans <= 80:
        return f"about {max(1, round(cans))} watering cans"
    return f"about {round(litres / DRUM_LITRES)} drums (200 L)"


def recommend(inp: EngineInput) -> dict:
    soil = inp.soil
    fc, wp, sat = soil["fc"], soil["wp"], soil["sat"]
    taw = (fc - wp) / 100.0 * inp.root_depth_mm

    # --- history nudge: a field that lost yield to a dry spell gets a slightly more cautious trigger
    p = inp.p
    history_caution = False
    if len(inp.yields) >= 2:
        newest, prev = inp.yields[0], inp.yields[1]
        if newest["dry_spell"] and prev["amount_kg"] > 0 and newest["amount_kg"] < 0.85 * prev["amount_kg"]:
            p = max(0.15, p - 0.05)
            history_caution = True

    days = (inp.today - inp.planting_date).days
    stage, kc, day_in_stage, days_to_next, next_stage = stage_for(inp.stages, days)
    sensitive = stage == inp.sensitive_stage
    raw = p * taw * (0.9 if sensitive else 1.0)  # trigger a little earlier in the sensitive stage

    # --- data availability
    have_weather = bool(inp.forecast)
    weather_stale = inp.weather_age_h is not None and inp.weather_age_h > 6
    have_moisture = inp.moisture is not None
    moisture_old = have_moisture and inp.moisture_age_h is not None and inp.moisture_age_h > 48

    theta = inp.moisture if have_moisture else fc - 0.5 * p * (fc - wp)
    depletion = max(0.0, (fc - theta) / 100.0 * inp.root_depth_mm)
    waterlogged = have_moisture and theta >= sat
    wet = depletion < 0.2 * raw

    d0 = inp.forecast[0] if have_weather else DayWeather(inp.today)
    d1 = inp.forecast[1] if len(inp.forecast) > 1 else DayWeather(inp.today)
    etc0 = d0.et0 * kc
    etc1 = d1.et0 * kc
    rain0, rain1 = effective_rain(d0), effective_rain(d1)

    ndvi_latest, ndvi_delta, ndvi_state = ndvi_trend(inp.ndvi)

    end_today = depletion + etc0 - rain0
    end_tomorrow = max(end_today, 0) + etc1 - rain1
    need_mm = _clamp(end_today, 0, taw)
    dry_and_falling = ndvi_state == "falling" and depletion >= 0.6 * raw
    wet_and_falling = ndvi_state == "falling" and (waterlogged or wet)

    # --- decision
    reasons = []
    if wet_and_falling:
        action = "WATCH"
        reasons.append(("NDVI_FALL_WET", {"delta": round(ndvi_delta, 2)}))
        if waterlogged:
            reasons.append(("WATERLOGGED", {"moisture": round(theta)}))
    elif waterlogged:
        action = "SKIP_TODAY"
        reasons.append(("WATERLOGGED", {"moisture": round(theta)}))
    elif not have_moisture and not have_weather:
        action = "WATCH"
        reasons.append(("NO_MOISTURE", {}))
        reasons.append(("NO_WEATHER", {}))
    else:
        hit_now = depletion >= raw
        hit_today = end_today >= raw or (dry_and_falling and end_today >= 0.8 * raw)
        rain_covers = rain0 >= 0.7 * max(need_mm, 1.0)
        if hit_now and not rain_covers:
            action = "IRRIGATE_NOW"
        elif hit_now and rain_covers:
            action = "SKIP_TODAY"
            reasons.append(("RAIN_COVERS", {"mm": round(rain0), "prob": round(d0.rain_prob)}))
        elif hit_today and not rain_covers:
            action = "IRRIGATE_LATER_TODAY"
        elif hit_today and rain_covers:
            action = "SKIP_TODAY"
            reasons.append(("RAIN_COVERS", {"mm": round(rain0), "prob": round(d0.rain_prob)}))
        else:
            action = "SKIP_TODAY"
            if rain0 + rain1 >= 5:
                reasons.append(("HEAVY_RAIN_SKIP", {"mm": round(rain0 + rain1), "prob": round(max(d0.rain_prob, d1.rain_prob))}))
            reasons.append(("SOIL_ENOUGH", {"moisture": round(theta), "left": round(max(raw - depletion, 0))}))
        if action.startswith("IRRIGATE"):
            reasons.append(("SOIL_DRY", {"moisture": round(theta), "pct": round(100 * depletion / raw) if raw else 0}))
            if etc0 >= 5:
                reasons.append(("HOT_DEMAND", {"etc": round(etc0, 1), "tmax": round(d0.tmax)}))
            if sensitive:
                reasons.append(("SENSITIVE_STAGE", {"stage": stage}))
            if dry_and_falling:
                reasons.append(("NDVI_FALL_DRY", {"delta": round(ndvi_delta, 2)}))
        if history_caution and action != "WATCH":
            reasons.append(("YIELD_CAUTION", {}))

    if weather_stale:
        reasons.append(("STALE_WEATHER", {"hours": round(inp.weather_age_h)}))
    if have_weather is False and have_moisture:
        reasons.append(("NO_WEATHER", {}))
    if not have_moisture and have_weather:
        reasons.append(("NO_MOISTURE", {}))
    if moisture_old:
        reasons.append(("STALE_MOISTURE", {"hours": round(inp.moisture_age_h)}))

    # --- volume and window
    if action.startswith("IRRIGATE"):
        depth = max(round(need_mm, 1), 3.0)
        if depth > MAX_EVENT_MM:
            depth = float(MAX_EVENT_MM)
            reasons.append(("SPLIT_WATERING", {"mm": MAX_EVENT_MM, "total": round(need_mm)}))
        litres = litres_for(depth, inp)
    else:
        depth, litres = 0.0, 0.0

    hot = d0.tmax >= 32
    if action == "IRRIGATE_NOW":
        window = "5:30 – 8:00 am" if inp.hour < 9 else ("5:00 – 7:00 pm" if inp.hour < 17 else "as soon as you can, before dark")
    elif action == "IRRIGATE_LATER_TODAY":
        window = "5:00 – 7:00 pm" if d0.rain_prob < 60 else "before 8 am, ahead of the rain"
    else:
        window = ""
    if hot and window.startswith("5:30"):
        window += " (before the heat)"

    # --- confidence
    score = 1.0
    notes = []
    if not have_moisture:
        score -= 0.40
        notes.append("No soil moisture reading")
    elif moisture_old:
        score -= 0.20
        notes.append("Soil moisture reading is old")
    elif inp.moisture_age_h and inp.moisture_age_h > 24:
        score -= 0.10
        notes.append("Soil moisture reading is over a day old")
    if not have_weather:
        score -= 0.40
        notes.append("No weather forecast")
    elif weather_stale:
        score -= 0.30
        notes.append("Weather forecast is out of date")
    if not inp.ndvi:
        score -= 0.10
        notes.append("No crop-stress (NDVI) data")
    confidence = "High" if score >= 0.8 else "Medium" if score >= 0.55 else "Low"

    # --- signals: score is the push toward irrigating (-1 skip ... +1 irrigate)
    def sig(key, label, display, status, push, weight):
        return {"key": key, "label": label, "display": display, "status": status, "push": round(push, 2), "weight": weight, "contribution": round(push * weight, 3)}

    ratio = depletion / raw if raw else 0
    signals = [
        sig("soil", "Soil moisture",
            f"{theta:.0f}% ({'estimated' if not have_moisture else 'simulated' if inp.moisture_simulated else 'measured'})",
            "stress" if ratio >= 1 else "watch" if ratio >= 0.7 else "good",
            _clamp(ratio * 2 - 1, -1, 1), 0.35 if have_moisture else 0.14),
        sig("rain", "Rain forecast",
            f"{rain0 + rain1:.0f} mm expected (today + tomorrow)" if have_weather else "No forecast",
            "info" if not have_weather else "good" if rain0 + rain1 >= 5 else "watch" if rain0 + rain1 >= 1 else "stress",
            -_clamp((rain0 + 0.5 * rain1) / max(etc0 * 1.5, 3.0), 0, 1) if have_weather else 0, 0.30 if have_weather else 0.05),
        sig("demand", "Crop water use",
            f"{etc0:.1f} mm/day ({stage}, Kc {kc:.2f})", "watch" if etc0 >= 5 else "good", _clamp((etc0 - 3.0) / 3.0, -1, 1), 0.15),
        sig("stage", "Growth stage",
            f"{stage.title()}, {days_to_next} days to {next_stage or 'harvest'}" if next_stage else f"{stage.title()} stage",
            "watch" if sensitive else "info", 0.6 if sensitive else (-0.2 if stage in ("initial", "late") else 0.1), 0.08),
        sig("ndvi", "Crop stress (NDVI)",
            (f"{ndvi_latest:.2f}, {ndvi_state}" + (" (simulated)" if inp.ndvi_simulated else "")) if ndvi_latest is not None else "No data",
            "stress" if dry_and_falling else "watch" if wet_and_falling else "good" if ndvi_state in ("stable", "rising") else "info",
            0.8 if dry_and_falling else (-0.5 if wet_and_falling else 0), 0.08 if inp.ndvi else 0.03),
        sig("history", "Last season",
            "Dry spell hurt yield: trigger set a little earlier" if history_caution else ("No adjustment" if inp.yields else "No yield history"),
            "watch" if history_caution else "info", 0.5 if history_caution else 0, 0.04),
    ]
    total = sum(abs(s["contribution"]) for s in signals) or 1.0
    for s in signals:
        s["share"] = round(abs(s["contribution"]) / total, 3)
        s["direction"] = "irrigate" if s["contribution"] > 0.005 else "skip" if s["contribution"] < -0.005 else "neutral"
    signals.sort(key=lambda s: -s["share"])

    # --- what if the farmer waits 24 hours
    if action.startswith("IRRIGATE"):
        if end_tomorrow >= taw * 0.9:
            risk, code = "high", "WAIT_HIGH"
        elif end_tomorrow >= raw:
            risk, code = "medium", "WAIT_MEDIUM"
        else:
            risk, code = "low", "WAIT_LOW"
        wait_mm = _clamp(end_tomorrow, 0, taw)
        what_if = {"risk": risk, "code": code, "tomorrow_mm": round(wait_mm, 1), "tomorrow_litres": round(litres_for(wait_mm, inp)), "stress_mm": round(max(end_tomorrow - raw, 0), 1)}
    elif action == "WATCH":
        what_if = {"risk": "low", "code": "WAIT_WATCH"}
    else:
        needed_tomorrow = end_tomorrow >= raw
        what_if = {"risk": "medium" if needed_tomorrow else "low", "code": "WAIT_SKIP_NEED" if needed_tomorrow else "WAIT_SKIP_FINE",
                   "tomorrow_mm": round(_clamp(end_tomorrow, 0, taw), 1), "tomorrow_litres": round(litres_for(_clamp(end_tomorrow, 0, taw), inp)),
                   "saved_litres": round(litres_for(_clamp(max(end_today, 0), 0, taw), inp))}

    reasons = [{"code": c, "p": prm} for c, prm in reasons]
    return {
        "action": action,
        "depth_mm": round(depth, 1),
        "volume_l": round(litres),
        "volume_human": human_volume(litres, inp.method),
        "window": window,
        "confidence": confidence,
        "confidence_score": round(_clamp(score, 0, 1), 2),
        "confidence_notes": notes,
        "signals": signals,
        "reasons": reasons,
        "what_if": what_if,
        "stage": {"name": stage, "kc": kc, "day": day_in_stage, "days_to_next": days_to_next, "next": next_stage, "sensitive": sensitive},
        "balance": {
            "theta": round(theta, 1), "fc": fc, "wp": wp, "sat": sat, "taw_mm": round(taw, 1), "raw_mm": round(raw, 1),
            "depletion_mm": round(depletion, 1), "etc_mm": round(etc0, 1), "rain_today_mm": round(rain0, 1),
            "rain_tomorrow_mm": round(rain1, 1), "end_today_mm": round(end_today, 1), "end_tomorrow_mm": round(end_tomorrow, 1),
            "trigger_pct": round(fc - raw / inp.root_depth_mm * 100, 1) if inp.root_depth_mm else None,
        },
        "ndvi": {"latest": ndvi_latest, "delta": round(ndvi_delta, 3), "state": ndvi_state, "simulated": inp.ndvi_simulated},
        "inputs": {
            "moisture_simulated": inp.moisture_simulated, "weather_demo": inp.weather_demo, "weather_age_h": inp.weather_age_h,
            "moisture_age_h": inp.moisture_age_h, "have_moisture": have_moisture, "have_weather": have_weather,
            "area_m2": inp.area_m2, "efficiency": inp.efficiency, "method": inp.method,
            "can_depth_mm": round(CAN_LITRES * inp.efficiency / inp.area_m2, 3) if inp.area_m2 else 0,
            "rain_prob_today": d0.rain_prob, "tmax": d0.tmax,
        },
    }
