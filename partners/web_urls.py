from django.urls import path

from .web_views import (
    customer_create,
    customer_list,
    customer_update,
    supplier_create,
    supplier_list,
    supplier_update,
)


app_name = "partners_web"


urlpatterns = [
    path(
        "customers/",
        customer_list,
        name="customer-list",
    ),
    path(
        "customers/add/",
        customer_create,
        name="customer-create",
    ),
    path(
        "customers/<int:pk>/edit/",
        customer_update,
        name="customer-update",
    ),
    path(
        "suppliers/",
        supplier_list,
        name="supplier-list",
    ),
    path(
        "suppliers/add/",
        supplier_create,
        name="supplier-create",
    ),
    path(
        "suppliers/<int:pk>/edit/",
        supplier_update,
        name="supplier-update",
    ),
]
