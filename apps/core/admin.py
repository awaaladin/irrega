from django.contrib import admin

from apps.billing.models import Invoice, Plan, Subscription
from apps.farms.models import Crop, Farm, Field
from apps.partners.models import Organization, PilotCode

admin.site.register([Crop, Farm, Field, Plan, Subscription, Invoice, Organization, PilotCode])
