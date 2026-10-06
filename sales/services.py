from uuid import uuid4

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from inventory.models import (
    Stock,
    StockMovement,
    StockReservation,
)

from .exceptions import (
    InsufficientStock,
    InvalidSalesOrderStatus,
)
from .models import SalesOrder, SalesOrderItem


@transaction.atomic
def create_sales_order(
    *,
    created_by,
    customer,
    warehouse,
    items,
):
    temporary_number = f"TMP-{uuid4().hex[:20]}"

    order = SalesOrder.objects.create(
        created_by=created_by,
        customer=customer,
        warehouse=warehouse,
        order_number=temporary_number,
    )

    order.order_number = f"SO-{timezone.now().year}-{order.id:06d}"

    order.save(
        update_fields=(
            "order_number",
            "updated_at",
        )
    )

    for item_data in items:
        SalesOrderItem.objects.create(
            sales_order=order,
            **item_data,
        )

    return order


@transaction.atomic
def confirm_sales_order(*, order_id):
    order = SalesOrder.objects.select_for_update().get(pk=order_id)

    if order.status != SalesOrder.Status.DRAFT:
        raise InvalidSalesOrderStatus("Only a DRAFT sales order can be confirmed.")

    items = order.items.order_by("product_id")

    if not items.exists():
        raise InvalidSalesOrderStatus("Sales order must contain at least one item.")

    for item in items:
        try:
            stock = Stock.objects.select_for_update().get(
                product=item.product,
                warehouse=order.warehouse,
            )
        except Stock.DoesNotExist:
            raise InsufficientStock(
                f"No stock exists for product {item.product.sku} "
                f"in warehouse {order.warehouse.code}."
            )

        reserved_quantity = (
            StockReservation.objects.filter(
                stock=stock,
                status=StockReservation.Status.ACTIVE,
            ).aggregate(total=Sum("quantity"))["total"]
            or 0
        )

        available_quantity = stock.quantity - reserved_quantity

        if item.quantity > available_quantity:
            raise InsufficientStock(
                f"Insufficient stock for product {item.product.sku}. "
                f"Available: {available_quantity}, "
                f"requested: {item.quantity}."
            )

        StockReservation.objects.create(
            sales_order_item=item,
            stock=stock,
            quantity=item.quantity,
            status=StockReservation.Status.ACTIVE,
        )

    order.status = SalesOrder.Status.CONFIRMED
    order.confirmed_at = timezone.now()

    order.save(
        update_fields=(
            "status",
            "confirmed_at",
            "updated_at",
        )
    )

    return order


@transaction.atomic
def cancel_sales_order(*, order_id):
    order = SalesOrder.objects.select_for_update().get(pk=order_id)

    if order.status not in {
        SalesOrder.Status.DRAFT,
        SalesOrder.Status.CONFIRMED,
    }:
        raise InvalidSalesOrderStatus(
            "Only DRAFT or CONFIRMED sales orders can be cancelled."
        )

    if order.status == SalesOrder.Status.CONFIRMED:
        reservations = StockReservation.objects.select_for_update().filter(
            sales_order_item__sales_order=order,
            status=StockReservation.Status.ACTIVE,
        )

        now = timezone.now()

        for reservation in reservations:
            reservation.status = StockReservation.Status.RELEASED
            reservation.released_at = now
            reservation.save(
                update_fields=(
                    "status",
                    "released_at",
                )
            )

    order.status = SalesOrder.Status.CANCELLED
    order.cancelled_at = timezone.now()

    order.save(
        update_fields=(
            "status",
            "cancelled_at",
            "updated_at",
        )
    )

    return order


@transaction.atomic
def start_processing_sales_order(*, order_id):
    order = SalesOrder.objects.select_for_update().get(pk=order_id)

    if order.status != SalesOrder.Status.CONFIRMED:
        raise InvalidSalesOrderStatus(
            "Only a CONFIRMED sales order can start processing."
        )

    order.status = SalesOrder.Status.PROCESSING

    order.save(
        update_fields=(
            "status",
            "updated_at",
        )
    )

    return order


@transaction.atomic
def ship_sales_order(*, order_id, performed_by):
    order = SalesOrder.objects.select_for_update().get(pk=order_id)

    if order.status != SalesOrder.Status.PROCESSING:
        raise InvalidSalesOrderStatus("Only a PROCESSING sales order can be shipped.")

    reservations = (
        StockReservation.objects.select_for_update()
        .select_related(
            "stock",
            "sales_order_item",
        )
        .filter(
            sales_order_item__sales_order=order,
            status=StockReservation.Status.ACTIVE,
        )
        .order_by("stock_id")
    )

    if not reservations.exists():
        raise InvalidSalesOrderStatus("Sales order has no active stock reservations.")

    now = timezone.now()

    for reservation in reservations:
        stock = Stock.objects.select_for_update().get(pk=reservation.stock_id)

        if stock.quantity < reservation.quantity:
            raise InsufficientStock(
                f"Insufficient physical stock for product {stock.product.sku}."
            )

        stock.quantity -= reservation.quantity
        stock.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

        StockMovement.objects.create(
            stock=stock,
            movement_type=StockMovement.MovementType.SALES_SHIPMENT,
            quantity=-reservation.quantity,
            sales_order_item=reservation.sales_order_item,
            performed_by=performed_by,
        )

        reservation.status = StockReservation.Status.CONSUMED
        reservation.save(update_fields=("status",))

    order.status = SalesOrder.Status.SHIPPED
    order.shipped_at = now

    order.save(
        update_fields=(
            "status",
            "shipped_at",
            "updated_at",
        )
    )

    return order
