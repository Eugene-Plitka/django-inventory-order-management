from django.urls import path

from .web_views import (
    purchase_order_cancel,
    purchase_order_confirm,
    purchase_order_create,
    purchase_order_detail,
    purchase_order_list,
    purchase_order_receive,
    purchase_order_update,
)


app_name = "purchasing_web"


urlpatterns = [
    path(
        "purchase-orders/",
        purchase_order_list,
        name="purchase-order-list",
    ),
    path(
        "purchase-orders/add/",
        purchase_order_create,
        name="purchase-order-create",
    ),
    path(
        "purchase-orders/<int:pk>/",
        purchase_order_detail,
        name="purchase-order-detail",
    ),
    path(
        "purchase-orders/<int:pk>/edit/",
        purchase_order_update,
        name="purchase-order-update",
    ),
    path(
        "purchase-orders/<int:pk>/confirm/",
        purchase_order_confirm,
        name="purchase-order-confirm",
    ),
    path(
        "purchase-orders/<int:pk>/cancel/",
        purchase_order_cancel,
        name="purchase-order-cancel",
    ),
    path(
        "purchase-orders/<int:pk>/receive/",
        purchase_order_receive,
        name="purchase-order-receive",
    ),
]
