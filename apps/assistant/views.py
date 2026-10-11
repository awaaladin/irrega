import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, StreamingHttpResponse
from django.views.decorators.http import require_POST

from apps.decisions.models import Decision
from apps.engine.services import get_recommendation
from apps.farms.models import Field
from apps.providers import llm, weather

from .models import ChatMessage


def build_facts(field, rec, user):
    p = rec.payload
    reading = field.readings.first()
    snap = weather.latest(field.farm)
    return {
        "field": {"id": field.pk, "name": field.name, "crop": field.crop.name, "soil": field.soil, "area_ha": field.area_ha, "method": field.method},
        "recommendation": p,
        "latest_soil_reading": {"value_pct": reading.value, "taken_at": reading.taken_at.isoformat(), "source": reading.source} if reading else None,
        "forecast_next_days": snap.days[:4] if snap else None,
        "forecast_is_demo_data": bool(snap and snap.is_demo),
        "recent_decisions": [{"kind": d.kind, "farmer_action": d.farmer_action, "date": d.created.date().isoformat()}
                             for d in Decision.objects.filter(recommendation__field=field).order_by("-created")[:5]],
        "watering_can_litres": 15,
    }


@login_required
@require_POST
def ask(request):
    try:
        data = json.loads(request.body or "{}")
        field = Field.objects.select_related("crop", "farm").get(pk=data.get("field"), farm__owner=request.user)
    except (Field.DoesNotExist, ValueError, TypeError, json.JSONDecodeError):
        return HttpResponse("I could not find that field.", status=404)
    q = (data.get("question") or "").strip()[:500]
    if not q:
        return HttpResponse("Ask me something about this field.", status=400)
    rec = get_recommendation(field)
    facts = build_facts(field, rec, request.user)
    history = [{"role": m.role, "text": m.text} for m in ChatMessage.objects.filter(field=field, user=request.user).order_by("-id")[:6][::-1]]
    ChatMessage.objects.create(field=field, user=request.user, role="user", text=q)
    provider = llm.get_provider()

    def gen():
        parts = []
        try:
            for chunk in provider.stream(q, facts, request.user.language, history):
                parts.append(chunk)
                yield chunk
        except Exception:
            # Claude unreachable: fall back to the grounded template so the farmer still gets an honest answer
            parts.clear()
            for chunk in llm.TemplateProvider().stream(q, facts, request.user.language, history):
                parts.append(chunk)
                yield chunk
        ChatMessage.objects.create(field=field, user=request.user, role="assistant", text="".join(parts))

    resp = StreamingHttpResponse(gen(), content_type="text/plain; charset=utf-8")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp
