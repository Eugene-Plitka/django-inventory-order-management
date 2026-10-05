from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "supplier",
        "warehouse",
        "status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "warehouse",
    )

    search_fields = (
        "order_number",
        "supplier__name",
    )

    inlines = [PurchaseOrderItemInline]
