from django.contrib import admin

from .models import Customer, Supplier


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "contact_person",
        "email",
        "phone",
        "is_active",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "contact_person",
        "email",
        "phone",
        "tax_id",
    )


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "contact_person",
        "email",
        "phone",
        "is_active",
    )

    list_filter = ("is_active",)

    search_fields = (
        "name",
        "contact_person",
        "email",
        "phone",
        "tax_id",
    )
