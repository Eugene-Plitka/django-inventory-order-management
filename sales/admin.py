from django.contrib import admin

from .models import SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order_number",
        "customer",
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
        "customer__name",
    )

    inlines = [SalesOrderItemInline]
