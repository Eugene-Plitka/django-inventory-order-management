from django.db import models

# Create your models here.
from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        SALES_ORDER_CONFIRMED = (
            "SALES_ORDER_CONFIRMED",
            "Sales Order Confirmed",
        )

        SALES_ORDER_SHIPPED = (
            "SALES_ORDER_SHIPPED",
            "Sales Order Shipped",
        )

        PURCHASE_ORDER_CONFIRMED = (
            "PURCHASE_ORDER_CONFIRMED",
            "Purchase Order Confirmed",
        )

        PURCHASE_ORDER_RECEIVED = (
            "PURCHASE_ORDER_RECEIVED",
            "Purchase Order Received",
        )

        LOW_STOCK = (
            "LOW_STOCK",
            "Low Stock",
        )

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=40,
        choices=Type.choices,
    )

    title = models.CharField(
        max_length=150,
    )

    message = models.CharField(
        max_length=300,
    )

    url = models.CharField(
        max_length=255,
        blank=True,
    )

    is_read = models.BooleanField(
        default=False,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ("-created_at",)

        indexes = [
            models.Index(
                fields=(
                    "recipient",
                    "is_read",
                    "created_at",
                )
            ),
        ]

    def __str__(self):
        return f"{self.recipient}: {self.title}"
