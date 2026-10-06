from django.urls import path

from .web_views import (
    category_create,
    category_list,
    category_update,
    manufacturer_create,
    manufacturer_list,
    manufacturer_update,
    product_create,
    product_list,
    product_update,
)


app_name = "catalog_web"


urlpatterns = [
    path(
        "products/",
        product_list,
        name="product-list",
    ),
    path(
        "products/add/",
        product_create,
        name="product-create",
    ),
    path(
        "products/<int:pk>/edit/",
        product_update,
        name="product-update",
    ),
    path(
        "categories/",
        category_list,
        name="category-list",
    ),
    path(
        "categories/add/",
        category_create,
        name="category-create",
    ),
    path(
        "categories/<int:pk>/edit/",
        category_update,
        name="category-update",
    ),
    path(
        "manufacturers/",
        manufacturer_list,
        name="manufacturer-list",
    ),
    path(
        "manufacturers/add/",
        manufacturer_create,
        name="manufacturer-create",
    ),
    path(
        "manufacturers/<int:pk>/edit/",
        manufacturer_update,
        name="manufacturer-update",
    ),
]
