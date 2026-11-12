from django.contrib import admin

from .models import Supplier, Purchase, PurchaseItem


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "purchase_number",
        "tenant",
        "supplier",
        "status",
        "grand_total",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("purchase_number", "supplier_invoice_number")
    inlines = [PurchaseItemInline]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name", "tenant", "phone", "gstin", "is_active")
    search_fields = ("name", "phone")
    list_filter = ("is_active",)