from uuid import uuid4

from django.db import IntegrityError, transaction
from django.utils import timezone

from inventory.models import Stock, StockMovement
from notifications.services import (
    notify_purchase_order_confirmed,
    notify_purchase_order_received,
    schedule_notification,
)

from .models import PurchaseOrder, PurchaseOrderItem


class PurchaseOrderServiceError(Exception):
    pass


class InvalidPurchaseOrderStatus(PurchaseOrderServiceError):
    pass


@transaction.atomic
def create_purchase_order(
    *,
    created_by,
    supplier,
    warehouse,
    items,
):
    temporary_number = f"TMP-{uuid4().hex[:20]}"

    order = PurchaseOrder.objects.create(
        created_by=created_by,
        supplier=supplier,
        warehouse=warehouse,
        order_number=temporary_number,
    )

    order.order_number = f"PO-{timezone.now().year}-{order.id:06d}"

    order.save(
        update_fields=(
            "order_number",
            "updated_at",
        )
    )

    for item_data in items:
        PurchaseOrderItem.objects.create(
            purchase_order=order,
            **item_data,
        )

    return order


@transaction.atomic
def update_purchase_order(
    *,
    order_id,
    supplier=None,
    warehouse=None,
    items=None,
):
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)

    if order.status != PurchaseOrder.Status.DRAFT:
        raise InvalidPurchaseOrderStatus("Only a DRAFT purchase order can be edited.")

    update_fields = []

    if supplier is not None:
        order.supplier = supplier
        update_fields.append("supplier")

    if warehouse is not None:
        order.warehouse = warehouse
        update_fields.append("warehouse")

    if items is not None:
        order.items.all().delete()

        for item_data in items:
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                **item_data,
            )

    if update_fields or items is not None:
        update_fields.append("updated_at")

        order.save(update_fields=update_fields)

    return order


@transaction.atomic
def confirm_purchase_order(*, order_id):
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)

    if order.status != PurchaseOrder.Status.DRAFT:
        raise InvalidPurchaseOrderStatus(
            "Only a DRAFT purchase order can be confirmed."
        )

    if not order.items.exists():
        raise InvalidPurchaseOrderStatus(
            "Purchase order must contain at least one item."
        )

    order.status = PurchaseOrder.Status.CONFIRMED
    order.confirmed_at = timezone.now()

    order.save(
        update_fields=(
            "status",
            "confirmed_at",
            "updated_at",
        )
    )

    schedule_notification(
        notify_purchase_order_confirmed,
        order,
    )

    return order


def _get_or_create_locked_stock(*, product, warehouse):
    try:
        return Stock.objects.select_for_update().get(
            product=product,
            warehouse=warehouse,
        )
    except Stock.DoesNotExist:
        try:
            with transaction.atomic():
                Stock.objects.create(
                    product=product,
                    warehouse=warehouse,
                    quantity=0,
                    reorder_level=0,
                )
        except IntegrityError:
            # Another transaction created the same stock row first.
            pass

        return Stock.objects.select_for_update().get(
            product=product,
            warehouse=warehouse,
        )


@transaction.atomic
def receive_purchase_order(*, order_id, performed_by):
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)

    if order.status != PurchaseOrder.Status.CONFIRMED:
        raise InvalidPurchaseOrderStatus(
            "Only a CONFIRMED purchase order can be received."
        )

    items = order.items.order_by("product_id")

    for item in items:
        stock = _get_or_create_locked_stock(
            product=item.product,
            warehouse=order.warehouse,
        )

        stock.quantity += item.quantity

        stock.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

        StockMovement.objects.create(
            stock=stock,
            movement_type=(StockMovement.MovementType.PURCHASE_RECEIPT),
            quantity=item.quantity,
            purchase_order_item=item,
            performed_by=performed_by,
        )

    order.status = PurchaseOrder.Status.RECEIVED
    order.received_at = timezone.now()

    order.save(
        update_fields=(
            "status",
            "received_at",
            "updated_at",
        )
    )

    schedule_notification(
        notify_purchase_order_received,
        order,
    )

    return order


@transaction.atomic
def cancel_purchase_order(*, order_id):
    order = PurchaseOrder.objects.select_for_update().get(pk=order_id)

    if order.status not in {
        PurchaseOrder.Status.DRAFT,
        PurchaseOrder.Status.CONFIRMED,
    }:
        raise InvalidPurchaseOrderStatus(
            "Only DRAFT or CONFIRMED purchase orders can be cancelled."
        )

    order.status = PurchaseOrder.Status.CANCELLED
    order.cancelled_at = timezone.now()

    order.save(
        update_fields=(
            "status",
            "cancelled_at",
            "updated_at",
        )
    )

    return order
