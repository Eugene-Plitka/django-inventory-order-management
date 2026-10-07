from django.db import models


class SystemSettings(models.Model):
    company_name = models.CharField(
        max_length=150,
        default="Django Inventory",
    )

    company_description = models.CharField(
        max_length=200,
        default="Auto Parts Wholesale",
    )

    sales_order_prefix = models.CharField(
        max_length=10,
        default="SO",
    )

    purchase_order_prefix = models.CharField(
        max_length=10,
        default="PO",
    )

    default_reorder_level = models.PositiveIntegerField(
        default=0,
    )

    low_stock_notifications_enabled = models.BooleanField(
        default=True,
    )

    order_notifications_enabled = models.BooleanField(
        default=True,
    )

    items_per_page = models.PositiveIntegerField(
        default=20,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        self.pk = 1

        super().save(
            *args,
            **kwargs,
        )

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)

        return obj

    def __str__(self):
        return "System Settings"
