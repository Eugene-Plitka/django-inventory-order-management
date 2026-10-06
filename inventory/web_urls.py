from django.urls import path

from .web_views import (
    movement_list,
    reservation_list,
    stock_adjust,
    stock_list,
    warehouse_create,
    warehouse_list,
    warehouse_update,
)


app_name = "inventory_web"


urlpatterns = [
    path(
        "warehouses/",
        warehouse_list,
        name="warehouse-list",
    ),
    path(
        "warehouses/add/",
        warehouse_create,
        name="warehouse-create",
    ),
    path(
        "warehouses/<int:pk>/edit/",
        warehouse_update,
        name="warehouse-update",
    ),
    path(
        "stock/",
        stock_list,
        name="stock-list",
    ),
    path(
        "stock/<int:pk>/adjust/",
        stock_adjust,
        name="stock-adjust",
    ),
    path(
        "reservations/",
        reservation_list,
        name="reservation-list",
    ),
    path(
        "stock-movements/",
        movement_list,
        name="movement-list",
    ),
]
