"""Crop library (FAO-56 style). Stage = [name, days, kc]. Add a crop here or in the admin; no code changes elsewhere."""

STAGE_NAMES = ["initial", "development", "mid", "late"]

CROPS = [
    # key, name, stages, root_depth_mm, p (depletion fraction), most water-sensitive stage, glyph
    ("cassava", "Cassava", [["initial", 30, 0.30], ["development", 60, 0.70], ["mid", 120, 0.80], ["late", 90, 0.50]], 800, 0.60, "mid", "cassava"),
    ("yam", "Yam", [["initial", 30, 0.40], ["development", 60, 0.80], ["mid", 90, 1.05], ["late", 60, 0.70]], 600, 0.50, "mid", "yam"),
    ("maize", "Maize", [["initial", 20, 0.30], ["development", 35, 0.80], ["mid", 40, 1.20], ["late", 30, 0.60]], 700, 0.55, "mid", "maize"),
    ("rice", "Rice", [["initial", 25, 1.05], ["development", 30, 1.10], ["mid", 40, 1.20], ["late", 30, 0.90]], 300, 0.20, "mid", "rice"),
    ("plantain", "Plantain", [["initial", 60, 0.50], ["development", 90, 0.90], ["mid", 120, 1.10], ["late", 60, 1.00]], 700, 0.35, "mid", "plantain"),
    ("tomato", "Tomato", [["initial", 25, 0.60], ["development", 30, 0.90], ["mid", 40, 1.15], ["late", 25, 0.80]], 500, 0.40, "mid", "tomato"),
    ("pepper", "Pepper", [["initial", 25, 0.60], ["development", 35, 0.90], ["mid", 40, 1.05], ["late", 20, 0.85]], 500, 0.30, "mid", "pepper"),
    ("okra", "Okra", [["initial", 15, 0.40], ["development", 25, 0.80], ["mid", 40, 1.05], ["late", 20, 0.85]], 600, 0.50, "mid", "okra"),
    ("cucumber", "Cucumber", [["initial", 20, 0.50], ["development", 30, 0.80], ["mid", 40, 1.00], ["late", 15, 0.75]], 450, 0.50, "mid", "leaf"),
    ("waterleaf", "Waterleaf", [["initial", 10, 0.50], ["development", 15, 0.80], ["mid", 30, 1.00], ["late", 15, 0.90]], 250, 0.30, "mid", "leaf"),
    ("cocoa", "Cocoa seedlings", [["initial", 60, 0.90], ["development", 120, 1.00], ["mid", 180, 1.05], ["late", 60, 1.00]], 600, 0.40, "development", "leaf"),
]


def ensure_crops(**kwargs):
    """Create missing crops. Runs after migrate; never overwrites edits made in the admin."""
    from .models import Crop

    for key, name, stages, root, p, sensitive, glyph in CROPS:
        Crop.objects.get_or_create(
            key=key,
            defaults=dict(name=name, stages=stages, root_depth_mm=root, depletion_fraction=p, sensitive_stage=sensitive, glyph=glyph),
        )


def growth_stage(stages, days_since_planting):
    """Return (stage_name, kc, day_in_stage, days_to_next, next_stage_name). Past the season stays in 'late'."""
    d = max(days_since_planting, 0)
    elapsed = 0
    for i, (name, days, kc) in enumerate(stages):
        if d < elapsed + days:
            nxt = stages[i + 1][0] if i + 1 < len(stages) else None
            return name, kc, d - elapsed, (elapsed + days) - d, nxt
        elapsed += days
    name, _, kc = stages[-1]
    return name, kc, d - elapsed, 0, None
