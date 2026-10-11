from django.test import Client
from django.contrib.auth import get_user_model
U = get_user_model()
c = Client(HTTP_HOST="localhost")
farmer = U.objects.get(username="demo@irrigation.test")
c.force_login(farmer)
from apps.farms.models import Field
fid = Field.objects.filter(farm__owner=farmer).first().pk
paths = ["/", "/farms/", f"/farms/fields/{fid}/", f"/farms/fields/{fid}/edit/", "/farms/onboarding/", "/insights/", "/notifications/",
         "/notifications/settings/", "/notifications/sent/", "/billing/", "/pilot/", "/account/", "/design/", "/offline/", "/manifest.webmanifest", "/sw.js"]
for p in paths:
    try:
        r = c.get(p)
        print(r.status_code, p, len(r.content))
        if r.status_code >= 500: print(r.content[:500])
    except Exception as e:
        print("ERR", p, type(e).__name__, str(e)[:300])
p = U.objects.get(username="partner@irrigation.test"); c.force_login(p)
for path in ["/partners/", "/"]:
    r = c.get(path); print(r.status_code, path)
a = U.objects.get(username="admin@irrigation.test"); c.force_login(a)
r = c.get("/system/"); print(r.status_code, "/system/")
