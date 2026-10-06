from django.contrib.auth import get_user_model
from django.db import transaction

from .models import Notification


User = get_user_model()


def _active_users_in_role(role_name):
    return User.objects.filter(
        is_active=True,
        groups__name=role_name,
    ).distinct()


def create_notification(
    *,
    recipient,
    notification_type,
    title,
    message,
    url="",
):
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        url=url,
    )


def create_notification_for_role(
    *,
    role_name,
    notification_type,
    title,
    message,
    url="",
):
    notifications = [
        Notification(
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
            url=url,
        )
        for user in _active_users_in_role(role_name)
    ]

    if notifications:
        Notification.objects.bulk_create(notifications)


def notify_sales_order_confirmed(order):
    url = f"/sales-orders/{order.pk}/"

    create_notification_for_role(
        role_name="Warehouse Employee",
        notification_type=(Notification.Type.SALES_ORDER_CONFIRMED),
        title="Sales order confirmed",
        message=(f"{order.order_number} is ready for warehouse processing."),
        url=url,
    )


def notify_sales_order_shipped(order):
    if not order.created_by.is_active:
        return

    create_notification(
        recipient=order.created_by,
        notification_type=(Notification.Type.SALES_ORDER_SHIPPED),
        title="Sales order shipped",
        message=(f"{order.order_number} has been shipped."),
        url=(f"/sales-orders/{order.pk}/"),
    )


def notify_purchase_order_confirmed(order):
    create_notification_for_role(
        role_name="Warehouse Employee",
        notification_type=(Notification.Type.PURCHASE_ORDER_CONFIRMED),
        title="Purchase order confirmed",
        message=(f"{order.order_number} is expected at {order.warehouse.code}."),
        url=(f"/purchase-orders/{order.pk}/"),
    )


def notify_purchase_order_received(order):
    if not order.created_by.is_active:
        return

    create_notification(
        recipient=order.created_by,
        notification_type=(Notification.Type.PURCHASE_ORDER_RECEIVED),
        title="Purchase order received",
        message=(f"{order.order_number} has been received."),
        url=(f"/purchase-orders/{order.pk}/"),
    )


def notify_low_stock(stock):
    message = (
        f"{stock.product.sku} — "
        f"{stock.product.name} in "
        f"{stock.warehouse.code} is at "
        f"{stock.quantity} units. "
        f"Reorder level: {stock.reorder_level}."
    )

    for role_name in (
        "Administrator",
        "Purchasing Manager",
    ):
        users = _active_users_in_role(role_name)

        for user in users:
            already_exists = Notification.objects.filter(
                recipient=user,
                notification_type=(Notification.Type.LOW_STOCK),
                is_read=False,
                message=message,
            ).exists()

            if not already_exists:
                create_notification(
                    recipient=user,
                    notification_type=(Notification.Type.LOW_STOCK),
                    title="Low stock warning",
                    message=message,
                    url=(f"/stock/?search={stock.product.sku}"),
                )


def schedule_notification(callback, *args):
    transaction.on_commit(lambda: callback(*args))
