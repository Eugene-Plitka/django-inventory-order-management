from django.contrib import admin

from .models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "is_active",
        "created_at",
    )

    list_filter = ("is_active",)

    search_fields = (
        "code",
        "name",
        "address",
    )


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "warehouse",
        "quantity",
        "reorder_level",
        "updated_at",
    )

    list_filter = ("warehouse",)

    search_fields = (
        "product__sku",
        "product__name",
        "warehouse__code",
        "warehouse__name",
    )

    readonly_fields = (
        "quantity",
        "created_at",
        "updated_at",
    )


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sales_order_item",
        "stock",
        "quantity",
        "status",
        "created_at",
        "released_at",
    )

    list_filter = (
        "status",
        "stock__warehouse",
    )

    search_fields = (
        "sales_order_item__sales_order__order_number",
        "stock__product__sku",
        "stock__product__name",
    )

    readonly_fields = (
        "sales_order_item",
        "stock",
        "quantity",
        "status",
        "created_at",
        "released_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "movement_type",
        "stock",
        "quantity",
        "performed_by",
        "created_at",
    )

    list_filter = (
        "movement_type",
        "stock__warehouse",
    )

    search_fields = (
        "stock__product__sku",
        "stock__product__name",
        "sales_order_item__sales_order__order_number",
        "purchase_order_item__purchase_order__order_number",
        "reason",
    )

    readonly_fields = (
        "stock",
        "movement_type",
        "quantity",
        "sales_order_item",
        "purchase_order_item",
        "reason",
        "performed_by",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
