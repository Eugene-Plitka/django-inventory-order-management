from django.contrib import admin

from .models import Category, Manufacturer, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "created_at")
    search_fields = ("name", "slug")


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "country", "created_at")
    search_fields = ("name", "country")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "name",
        "category",
        "manufacturer",
        "sale_price",
        "is_active",
    )

    list_filter = (
        "is_active",
        "category",
        "manufacturer",
    )

    search_fields = (
        "sku",
        "name",
    )
