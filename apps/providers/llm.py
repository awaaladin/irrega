"""LLMProvider: Claude when ANTHROPIC_API_KEY is set, deterministic grounded templates otherwise.
The model may only use the facts passed in `facts`. It must say when it does not know."""
import json
import logging
import re

import requests
from django.conf import settings

log = logging.getLogger(__name__)

SYSTEM = """You are the advisor inside Routine Irrigation Technology, helping a small farmer in Calabar South, Nigeria.
Answer ONLY from the FACTS JSON. Never invent readings, forecasts, prices or agronomy numbers that are not in the FACTS.
If the FACTS do not answer the question, say plainly that you do not know and what the farmer could check or add.
The farmer decides; you advise. Keep answers short (under 120 words), warm and plain. Use litres, mm and watering cans.
If language is 'pcm', answer in simple Nigerian Pidgin. State confidence honestly. Mention when data is simulated (demo)."""


class LLMProvider:
    name = "base"

    def stream(self, question, facts, lang="en", history=()):
        raise NotImplementedError


class TemplateProvider(LLMProvider):
    """Deterministic answers built from the engine output. Used when no API key is configured."""

    name = "template"

    def stream(self, question, facts, lang="en", history=()):
        text = self.answer(question, facts, lang)
        for word in re.findall(r"\S+\s*", text):
            yield word

    def answer(self, q, f, lang):
        from apps.engine import explain

        rec = f["recommendation"]
        ql = q.lower()
        pcm = lang == "pcm"
        m = re.search(r"(\d+)\s*(watering\s*)?cans?", ql)
        if m:
            cans = int(m.group(1))
            depth = cans * rec["inputs"]["can_depth_mm"]
            need = rec["balance"]["end_today_mm"]
            share = min(100, round(100 * depth / need)) if need > 0 else 100
            if rec["action"].startswith("IRRIGATE"):
                return (f"{cans} cans put about {depth:.1f} mm on {f['field']['name']}. The full recommendation is {rec['depth_mm']} mm, so that is roughly {share}% of it. "
                        f"Put them on the driest part first, in the {rec['window']} window, and check the soil again tomorrow.")
            return f"{f['field']['name']} does not need water today, so {cans} cans are not needed. If you still water, {cans} cans give about {depth:.1f} mm."
        if any(k in ql for k in ("wait", "tomorrow", "delay", "later")):
            return explain.what_if_text(rec, lang)
        if any(k in ql for k in ("stress", "healthy", "ndvi", "sick", "leaf", "leaves", "yellow")):
            n = rec["ndvi"]
            if n["latest"] is None:
                return "I do not have crop-stress (satellite) data for this field yet, so I cannot say. Look at the leaves in the morning: curling or drooping usually means thirst."
            sim = " This is simulated demo data." if n["simulated"] else ""
            if n["state"] == "falling" and rec["action"] == "WATCH":
                return f"Greenness is {n['latest']:.2f} and falling, but the soil is wet, so this is probably not thirst. Check for disease, pests, drainage or nutrients.{sim}"
            if n["state"] == "falling":
                return f"Greenness is {n['latest']:.2f} and falling while the soil is dry. That fits water stress, so watering as advised should help.{sim}"
            return f"Greenness is {n['latest']:.2f} and {n['state']}. I see no sign of stress from the satellite signal.{sim}"
        if any(k in ql for k in ("why", "reason", "explain", "how come")):
            return " ".join(explain.reason_texts(rec["reasons"], lang)[:3]) or explain.headline(rec, lang)
        if any(k in ql for k in ("how much", "litre", "liter", "volume", "water do")):
            return explain.headline(rec, lang)
        if "confiden" in ql or "sure" in ql:
            notes = "; ".join(rec["confidence_notes"]) or "all key data is fresh"
            return f"Confidence is {rec['confidence']}: {notes}."
        return ("I can only answer from this field's readings, forecast and crop stage. I do not have anything on that. "
                "Try: Why this? What if I wait a day? How much if I only have 5 cans? Is my crop stressed?")


class AnthropicProvider(LLMProvider):
    name = "claude"

    def stream(self, question, facts, lang="en", history=()):
        messages = [{"role": m["role"], "content": m["text"]} for m in history][-6:]
        messages.append({"role": "user", "content": f"FACTS:\n{json.dumps(facts, default=str)}\n\nLANGUAGE: {lang}\nQUESTION: {question}"})
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": settings.ANTHROPIC_MODEL, "max_tokens": 400, "system": SYSTEM, "messages": messages, "stream": True},
            stream=True, timeout=30,
        )
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.startswith("data: "):
                try:
                    ev = json.loads(line[6:])
                except ValueError:
                    continue
                if ev.get("type") == "content_block_delta" and ev["delta"].get("type") == "text_delta":
                    yield ev["delta"]["text"]


def get_provider():
    return AnthropicProvider() if settings.ANTHROPIC_API_KEY else TemplateProvider()
