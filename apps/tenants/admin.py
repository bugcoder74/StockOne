from django.contrib import admin
from .models import Tenant, TenantMembership, Store

admin.site.register(Tenant)
admin.site.register(TenantMembership)
admin.site.register(Store)