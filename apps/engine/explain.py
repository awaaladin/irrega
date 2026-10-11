"""Plain-language explanations. Add a language by adding a dict to LANGS; the engine only emits codes + numbers."""

ACTION_LABEL = {
    "IRRIGATE_NOW": {"en": "Water now", "pcm": "Water am now"},
    "IRRIGATE_LATER_TODAY": {"en": "Water later today", "pcm": "Water am later today"},
    "SKIP_TODAY": {"en": "Skip today", "pcm": "No water am today"},
    "WATCH": {"en": "Watch closely", "pcm": "Dey look am well"},
}
ACTION_META = {
    # icon names map to the SVG sprite in templates/components/icons.html
    "IRRIGATE_NOW": {"icon": "drop-fill", "tone": "water"},
    "IRRIGATE_LATER_TODAY": {"icon": "sunset", "tone": "water"},
    "SKIP_TODAY": {"icon": "cloud-rain", "tone": "skip"},
    "WATCH": {"icon": "eye", "tone": "watch"},
}

REASONS = {
    "en": {
        "HEAVY_RAIN_SKIP": "Rain is likely ({prob}% chance, about {mm} mm over the next two days), so the soil will get water on its own.",
        "RAIN_COVERS": "About {mm} mm of rain is expected today ({prob}% chance). That covers what the crop needs.",
        "SOIL_ENOUGH": "The soil holds enough water for now ({moisture}% moisture, about {left} mm before the crop would feel dry).",
        "SOIL_DRY": "The soil is getting dry ({moisture}% moisture). It has used {pct}% of the water this crop can spare.",
        "HOT_DEMAND": "It is hot (up to {tmax}°C), so the crop is using about {etc} mm of water a day.",
        "SENSITIVE_STAGE": "The crop is in its {stage} stage, when water shortage hurts the harvest most.",
        "NDVI_FALL_DRY": "Satellite greenness is falling ({delta}) while the soil is dry. That fits water stress.",
        "NDVI_FALL_WET": "Satellite greenness is falling ({delta}) but the soil is wet. More water will not fix this. Check for disease, pests, poor drainage or nutrient problems.",
        "WATERLOGGED": "The soil is waterlogged ({moisture}% moisture). Roots need air, so do not add water.",
        "NO_MOISTURE": "There is no soil moisture reading, so we estimated it. Please add a reading for a firmer answer.",
        "NO_WEATHER": "We could not get a weather forecast, so this uses typical values for the season.",
        "STALE_WEATHER": "The weather forecast is {hours} hours old. It may have changed.",
        "STALE_MOISTURE": "The last soil reading is {hours} hours old. A fresh one would help.",
        "YIELD_CAUTION": "A dry spell cut last season's harvest on this field, so we are a little more careful here.",
        "SPLIT_WATERING": "The soil could take about {total} mm, but that much at once mostly runs off. Give {mm} mm now and check again tomorrow.",
    },
    "pcm": {
        "HEAVY_RAIN_SKIP": "Rain go likely fall ({prob}% chance, like {mm} mm for two days), so ground go get water by itself.",
        "RAIN_COVERS": "Like {mm} mm of rain dey come today ({prob}% chance). E don cover wetin the crop need.",
        "SOIL_ENOUGH": "The ground still get enough water ({moisture}% moisture, like {left} mm before crop go feel dry).",
        "SOIL_DRY": "The ground dey dry ({moisture}% moisture). Crop don use {pct}% of the water wey e fit spare.",
        "HOT_DEMAND": "Sun dey hot (up to {tmax}°C), so crop dey drink like {etc} mm water every day.",
        "SENSITIVE_STAGE": "Crop dey {stage} stage, na there water shortage dey hurt harvest pass.",
        "NDVI_FALL_DRY": "Satellite see say the green dey reduce ({delta}) and ground dry. E fit be water wahala.",
        "NDVI_FALL_WET": "Satellite see say the green dey reduce ({delta}) but ground wet. More water no go help. Check for sickness, pest, bad drainage or hungry soil.",
        "WATERLOGGED": "Water don soak the ground too much ({moisture}% moisture). Root need air, so no add water.",
        "NO_MOISTURE": "We no get soil moisture reading, so we guess am. Abeg add one make answer strong.",
        "NO_WEATHER": "We no fit get weather forecast, so we use normal values for this season.",
        "STALE_WEATHER": "The weather forecast don old by {hours} hours. E fit don change.",
        "STALE_MOISTURE": "The last soil reading don old by {hours} hours. New one go help.",
        "YIELD_CAUTION": "Dry spell cut last season harvest for this field, so we dey more careful here.",
        "SPLIT_WATERING": "The ground fit take like {total} mm, but if you pour am at once, plenty go run go. Give {mm} mm now, check am again tomorrow.",
    },
}

HEADLINES = {
    "en": {
        "IRRIGATE_NOW": "Water this field {when}. About {depth} mm ({human}) will bring the soil back to a good level.",
        "IRRIGATE_LATER_TODAY": "Water this field later today, {when}. About {depth} mm ({human}).",
        "SKIP_TODAY": "Skip watering today. Your crop does not need it yet.",
        "WATCH": "Do not add water yet. Look at the crop first.",
    },
    "pcm": {
        "IRRIGATE_NOW": "Water this field {when}. Like {depth} mm ({human}) go bring the ground back well.",
        "IRRIGATE_LATER_TODAY": "Water this field later today, {when}. Like {depth} mm ({human}).",
        "SKIP_TODAY": "No water am today. Crop no need am yet.",
        "WATCH": "No add water yet. Look the crop well first.",
    },
}

WHAT_IF = {
    "en": {
        "WAIT_LOW": "If you wait a day, the crop should still be fine, but you would need about {tomorrow_mm} mm tomorrow.",
        "WAIT_MEDIUM": "If you wait a day, the crop will go past its comfortable limit by about {stress_mm} mm. You would then need about {tomorrow_mm} mm ({tomorrow_litres:,} litres).",
        "WAIT_HIGH": "If you wait a day, the crop will be stressed. Yield can drop. You would need about {tomorrow_mm} mm ({tomorrow_litres:,} litres) and still lose some growth.",
        "WAIT_SKIP_NEED": "Skipping today is fine, but expect to water tomorrow (about {tomorrow_mm} mm, {tomorrow_litres:,} litres).",
        "WAIT_SKIP_FINE": "Tomorrow should be fine too. The soil still has room, so watering now would mostly be wasted.",
        "WAIT_WATCH": "Waiting a day costs little. Look at the crop again tomorrow and add a fresh soil reading.",
    },
    "pcm": {
        "WAIT_LOW": "If you wait one day, crop go still dey fine, but tomorrow you go need like {tomorrow_mm} mm.",
        "WAIT_MEDIUM": "If you wait one day, crop go pass the comfortable level by like {stress_mm} mm. You go need like {tomorrow_mm} mm ({tomorrow_litres:,} litres).",
        "WAIT_HIGH": "If you wait one day, crop go suffer. Harvest fit drop. You go need like {tomorrow_mm} mm ({tomorrow_litres:,} litres) and e still go lose small growth.",
        "WAIT_SKIP_NEED": "No water today na correct, but tomorrow you go water (like {tomorrow_mm} mm, {tomorrow_litres:,} litres).",
        "WAIT_SKIP_FINE": "Tomorrow go still dey fine. The ground still get room, so if you water now, most of am go waste.",
        "WAIT_WATCH": "To wait one day no cost much. Look the crop again tomorrow and add new soil reading.",
    },
}


def _lang(lang):
    return lang if lang in REASONS else "en"


def action_label(action, lang="en"):
    return ACTION_LABEL[action][_lang(lang)]


def reason_texts(reasons, lang="en"):
    table = REASONS[_lang(lang)]
    out = []
    for r in reasons:
        tpl = table.get(r["code"])
        if tpl:
            out.append(tpl.format(**r["p"]))
    return out


def headline(rec, lang="en"):
    lang = _lang(lang)
    texts = reason_texts(rec["reasons"], lang)
    why = texts[0] if texts else ""
    return HEADLINES[lang][rec["action"]].format(when=rec["window"] or "today", depth=rec["depth_mm"], human=rec["volume_human"] or "no water", why=why)


def what_if_text(rec, lang="en"):
    w = rec["what_if"]
    return WHAT_IF[_lang(lang)][w["code"]].format(**{k: w.get(k, 0) for k in ("tomorrow_mm", "tomorrow_litres", "stress_mm", "saved_litres")})


def present(rec, lang="en"):
    """Add display fields to a stored recommendation payload."""
    meta = ACTION_META[rec["action"]]
    return {
        **rec,
        "label": action_label(rec["action"], lang),
        "icon": meta["icon"],
        "tone": meta["tone"],
        "headline": headline(rec, lang),
        "reason_texts": reason_texts(rec["reasons"], lang),
        "what_if_text": what_if_text(rec, lang),
    }
