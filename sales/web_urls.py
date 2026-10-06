from django.urls import path

from .web_views import (
    sales_order_cancel,
    sales_order_confirm,
    sales_order_create,
    sales_order_detail,
    sales_order_list,
    sales_order_ship,
    sales_order_start_processing,
    sales_order_update,
)


app_name = "sales_web"


urlpatterns = [
    path(
        "sales-orders/",
        sales_order_list,
        name="sales-order-list",
    ),
    path(
        "sales-orders/add/",
        sales_order_create,
        name="sales-order-create",
    ),
    path(
        "sales-orders/<int:pk>/",
        sales_order_detail,
        name="sales-order-detail",
    ),
    path(
        "sales-orders/<int:pk>/edit/",
        sales_order_update,
        name="sales-order-update",
    ),
    path(
        "sales-orders/<int:pk>/confirm/",
        sales_order_confirm,
        name="sales-order-confirm",
    ),
    path(
        "sales-orders/<int:pk>/cancel/",
        sales_order_cancel,
        name="sales-order-cancel",
    ),
    path(
        "sales-orders/<int:pk>/start-processing/",
        sales_order_start_processing,
        name="sales-order-start-processing",
    ),
    path(
        "sales-orders/<int:pk>/ship/",
        sales_order_ship,
        name="sales-order-ship",
    ),
]
