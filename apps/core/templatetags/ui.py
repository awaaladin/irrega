from django import template
from django.utils.html import format_html

from apps.engine import explain

register = template.Library()

# Full literal class strings so Tailwind can see them. Colour is never the only signal: each tone also has an icon + label.
TONES = {
    "water": "border-water/40 bg-water/15 text-water",
    "skip": "border-skip/40 bg-skip/15 text-skip",
    "watch": "border-watch/40 bg-watch/15 text-watch",
    "stress": "border-stress/40 bg-stress/15 text-stress",
    "leaf": "border-leaf/40 bg-leaf/15 text-leaf",
    "neutral": "border-line bg-sunken text-mute",
}
TEXT = {"water": "text-water", "skip": "text-skip", "watch": "text-watch", "stress": "text-stress", "leaf": "text-leaf", "neutral": "text-mute"}
FILL = {"water": "bg-water", "skip": "bg-skip", "watch": "bg-watch", "stress": "bg-stress", "leaf": "bg-leaf", "neutral": "bg-mute"}
STATUS_TONE = {"good": "leaf", "watch": "watch", "stress": "stress", "info": "neutral"}


@register.simple_tag
def icon(name, cls="h-5 w-5"):
    return format_html(
        '<svg class="{} shrink-0 fill-none stroke-current" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><use href="#i-{}"/></svg>',
        cls, name,
    )


@register.simple_tag
def crop_icon(crop, cls="h-5 w-5"):
    return icon(getattr(crop, "glyph", "leaf"), cls)


@register.simple_tag
def action_meta(action, lang="en"):
    m = explain.ACTION_META[action]
    return {"label": explain.action_label(action, lang), "icon": m["icon"], "tone": m["tone"], "classes": TONES[m["tone"]], "text": TEXT[m["tone"]], "fill": FILL[m["tone"]]}


@register.simple_tag
def tone(name, kind="classes"):
    return {"classes": TONES, "text": TEXT, "fill": FILL}[kind].get(name, "")


@register.filter
def status_tone(status):
    return STATUS_TONE.get(status, "neutral")


@register.filter
def tone_classes(name):
    return TONES.get(name, TONES["neutral"])


@register.filter
def tone_text(name):
    return TEXT.get(name, TEXT["neutral"])


@register.filter
def tone_fill(name):
    return FILL.get(name, FILL["neutral"])


@register.filter
def num(value, digits=0):
    try:
        v = float(value)
    except (TypeError, ValueError):
        return value
    return f"{v:,.{int(digits)}f}"


@register.filter
def lookup(d, key):
    return d.get(key) if hasattr(d, "get") else ""


@register.filter
def times100(value):
    try:
        return round(float(value) * 100)
    except (TypeError, ValueError):
        return 0


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.simple_tag
def sparkline(values, w=120, h=32, lo=0.1, hi=0.95):
    """SVG path for a series. Returns '' for fewer than 2 points."""
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return ""
    step = w / (len(vals) - 1)
    pts = [(i * step, h - 2 - (max(lo, min(hi, v)) - lo) / (hi - lo) * (h - 4)) for i, v in enumerate(vals)]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


@register.simple_tag
def override_reasons():
    return [("already_watered", "Already watered"), ("rain_started", "Rain started"), ("no_water", "No water available"),
            ("know_my_soil", "I know my soil"), ("crop_looks_thirsty", "Crop looks thirsty"), ("other", "Other")]


@register.filter
def scale(value, maximum):
    """value as a percentage of maximum (0-100), for bar geometry."""
    try:
        return round(max(0.0, min(100.0, float(value) / float(maximum) * 100)), 1)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0


@register.filter
def rest(value):
    """100 - value, for 'right:' offsets in bar geometry."""
    try:
        return round(100 - float(value), 1)
    except (TypeError, ValueError):
        return 0


@register.filter
def over(value, limit):
    """True when value is a number greater than limit (e.g. reading age in hours)."""
    try:
        return float(value) > float(limit)
    except (TypeError, ValueError):
        return False


@register.filter
def unscore(value):
    return str(value).replace("_", " ")
