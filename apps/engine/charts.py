"""Chart geometry computed server-side so charts render with no JS and ship a data table for screen readers."""
from datetime import timedelta

from django.utils import timezone

W, H = 640, 220
PAD_L, PAD_R, PAD_T, PAD_B = 36, 12, 12, 24


def moisture_chart(field, rec, days=30):
    bal = rec["balance"]
    now = timezone.now()
    start = now - timedelta(days=days)
    rows = list(field.readings.filter(taken_at__gte=start).order_by("taken_at"))
    ymax = max([bal["sat"] + 6] + [r.value for r in rows])
    ymin = 0

    def x(t):
        return PAD_L + (t - start).total_seconds() / (days * 86400) * (W - PAD_L - PAD_R)

    def y(v):
        return PAD_T + (1 - (v - ymin) / (ymax - ymin)) * (H - PAD_T - PAD_B)

    trigger = bal["trigger_pct"] or bal["fc"]
    bands = [
        {"label": "Too dry", "tone": "stress", "y": y(trigger), "h": y(ymin) - y(trigger)},
        {"label": "Good range", "tone": "water", "y": y(bal["sat"]), "h": y(trigger) - y(bal["sat"])},
        {"label": "Waterlogged", "tone": "skip", "y": y(ymax), "h": y(bal["sat"]) - y(ymax)},
    ]
    pts = [(x(r.taken_at), y(r.value)) for r in rows]
    d = ("M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in pts)) if len(pts) > 1 else ""
    ticks = [{"v": v, "y": y(v)} for v in range(0, int(ymax) + 1, 10)]
    return {
        "w": W, "h": H, "pad_l": PAD_L, "plot_w": W - PAD_L - PAD_R, "bands": bands, "d": d,
        "dots": [{"x": a, "y": b, "v": r.value, "t": r.taken_at, "sim": r.is_simulated} for (a, b), r in zip(pts, rows)],
        "ticks": ticks, "trigger_y": y(trigger), "trigger": round(trigger, 1), "rows": rows[-12:][::-1], "count": len(rows),
        "any_simulated": any(r.is_simulated for r in rows),
    }
