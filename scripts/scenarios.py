from apps.demo import services
from apps.farms.models import Farm
from django.utils import timezone
farm = Farm.objects.filter(is_demo=True).first()
for sc in ("normal", "rainy", "dry", "normal"):
    services.apply_scenario(farm, sc)
    print("\n==", sc)
    for f in farm.fields.all():
        r = f.recommendations.get(date=timezone.localdate())
        print(f"  {f.name:22s} {r.action:22s} {r.depth_mm:5.1f} mm  {r.confidence:6s}  top: {r.payload['reasons'][0]['code'] if r.payload['reasons'] else '-'}")
