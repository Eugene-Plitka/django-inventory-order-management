from django.conf import settings
from django.db import models

from catalog.models import Product


class Warehouse(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Stock(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stocks",
    )

    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="stocks",
    )

    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["product", "warehouse"],
                name="unique_product_warehouse_stock",
            ),
        ]

    def __str__(self):
        return f"{self.product} @ {self.warehouse}"


class StockReservation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        RELEASED = "RELEASED", "Released"
        CONSUMED = "CONSUMED", "Consumed"

    sales_order_item = models.ForeignKey(
        "sales.SalesOrderItem",
        on_delete=models.CASCADE,
        related_name="reservations",
    )

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="reservations",
    )

    quantity = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="stock_reservation_quantity_gt_0",
            ),
        ]

    def __str__(self):
        return f"{self.sales_order_item} - {self.stock} - {self.quantity}"


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        PURCHASE_RECEIPT = "PURCHASE_RECEIPT", "Purchase Receipt"
        SALES_SHIPMENT = "SALES_SHIPMENT", "Sales Shipment"
        ADJUSTMENT_IN = "ADJUSTMENT_IN", "Adjustment In"
        ADJUSTMENT_OUT = "ADJUSTMENT_OUT", "Adjustment Out"

    stock = models.ForeignKey(
        Stock,
        on_delete=models.PROTECT,
        related_name="movements",
    )

    movement_type = models.CharField(
        max_length=30,
        choices=MovementType.choices,
    )

    quantity = models.IntegerField()

    sales_order_item = models.ForeignKey(
        "sales.SalesOrderItem",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
    )

    purchase_order_item = models.ForeignKey(
        "purchasing.PurchaseOrderItem",
        on_delete=models.PROTECT,
        related_name="stock_movements",
        null=True,
        blank=True,
    )

    reason = models.TextField(blank=True)

    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity=0),
                name="stock_movement_quantity_not_0",
            ),
        ]

    def __str__(self):
        return f"{self.movement_type} - {self.stock} - {self.quantity}"
