from django.contrib import admin

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

    def has_change_permission(self, request, obj=None):
        if obj and obj.status != PurchaseOrder.Status.DRAFT:
            return False

        return super().has_change_permission(
            request,
            obj,
        )

    def has_add_permission(self, request, obj=None):
        if obj and obj.status != PurchaseOrder.Status.DRAFT:
            return False

        return super().has_add_permission(
            request,
            obj,
        )

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status != PurchaseOrder.Status.DRAFT:
            return False

        return super().has_delete_permission(
            request,
            obj,
        )


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

    readonly_fields = (
        "order_number",
        "status",
        "created_by",
        "created_at",
        "updated_at",
        "confirmed_at",
        "received_at",
        "cancelled_at",
    )

    inlines = [PurchaseOrderItemInline]

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)

        if obj and obj.status != PurchaseOrder.Status.DRAFT:
            readonly.extend(
                [
                    "supplier",
                    "warehouse",
                ]
            )

        return readonly

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(
            request,
            obj,
        )

        if obj and obj.status != PurchaseOrder.Status.DRAFT:
            for inline in inline_instances:
                inline.max_num = 0
                inline.can_delete = False

        return inline_instances
