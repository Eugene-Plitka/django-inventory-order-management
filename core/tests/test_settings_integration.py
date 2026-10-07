from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from catalog.models import (
    Category,
    Manufacturer,
    Product,
)
from core.models import SystemSettings
from inventory.models import (
    Stock,
    Warehouse,
)
from notifications.models import Notification
from partners.models import Supplier
from purchasing.services import (
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
)


class DefaultReorderLevelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="settings-stock@example.com",
            password="StrongPass123!",
        )

        self.category = Category.objects.create(
            name="Filters",
            slug="settings-filters",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Settings Manufacturer",
        )

        self.product = Product.objects.create(
            sku="SETTINGS-001",
            name="Oil Filter",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price=Decimal("25.00"),
        )

        self.supplier = Supplier.objects.create(
            name="Settings Supplier",
        )

        self.warehouse = Warehouse.objects.create(
            name="Settings Warehouse",
            code="SET-WH",
        )

        settings = SystemSettings.load()

        settings.default_reorder_level = 8

        settings.save(
            update_fields=(
                "default_reorder_level",
                "updated_at",
            )
        )

    def test_new_stock_uses_default_reorder_level(self):
        order = create_purchase_order(
            created_by=self.user,
            supplier=self.supplier,
            warehouse=self.warehouse,
            items=[
                {
                    "product": self.product,
                    "quantity": 15,
                    "unit_price": Decimal("10.00"),
                }
            ],
        )

        confirm_purchase_order(order_id=order.pk)

        receive_purchase_order(
            order_id=order.pk,
            performed_by=self.user,
        )

        stock = Stock.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(
            stock.quantity,
            15,
        )

        self.assertEqual(
            stock.reorder_level,
            8,
        )


class ItemsPerPageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="pagination@example.com",
            password="StrongPass123!",
        )

        settings = SystemSettings.load()

        settings.items_per_page = 5

        settings.save(
            update_fields=(
                "items_per_page",
                "updated_at",
            )
        )

        for index in range(12):
            Notification.objects.create(
                recipient=self.user,
                notification_type=(Notification.Type.LOW_STOCK),
                title=f"Notification {index}",
                message=f"Message {index}",
            )

    def test_notification_page_uses_system_page_size(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("notifications:list"))

        self.assertEqual(
            response.status_code,
            200,
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(
            len(page_obj.object_list),
            5,
        )

        self.assertEqual(
            page_obj.paginator.count,
            12,
        )

        self.assertEqual(
            page_obj.paginator.num_pages,
            3,
        )
