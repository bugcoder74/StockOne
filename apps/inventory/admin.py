from django.contrib import admin
from .models import StockBalance, StockMovement

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    readonly_fields = [
        field.name for field in StockMovement._meta.fields
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(StockBalance)