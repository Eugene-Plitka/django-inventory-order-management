from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.services import setup_roles
from catalog.models import (
    Category,
    Manufacturer,
    Product,
)
from inventory.models import (
    Stock,
    StockMovement,
    Warehouse,
)
from partners.models import Supplier
from purchasing.models import PurchaseOrder
from purchasing.services import (
    confirm_purchase_order,
    create_purchase_order,
)


class PurchaseOrderWebLifecycleTests(TestCase):
    def setUp(self):
        setup_roles()

        self.purchasing_manager = User.objects.create_user(
            email="purchasing-web@example.com",
            password="StrongPass123!",
        )

        self.purchasing_manager.groups.add(Group.objects.get(name="Purchasing Manager"))

        self.warehouse_employee = User.objects.create_user(
            email="warehouse-purchase@example.com",
            password="StrongPass123!",
        )

        self.warehouse_employee.groups.add(Group.objects.get(name="Warehouse Employee"))

        self.category = Category.objects.create(
            name="Suspension",
            slug="suspension",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Bilstein",
        )

        self.product = Product.objects.create(
            sku="PO-WEB-001",
            name="Shock Absorber",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price=Decimal("180.00"),
            is_active=True,
        )

        self.supplier = Supplier.objects.create(
            name="Web Test Supplier",
            is_active=True,
        )

        self.warehouse = Warehouse.objects.create(
            name="Purchase Warehouse",
            code="PUR-WEB",
            is_active=True,
        )

        self.order = create_purchase_order(
            created_by=self.purchasing_manager,
            supplier=self.supplier,
            warehouse=self.warehouse,
            items=[
                {
                    "product": self.product,
                    "quantity": 7,
                    "unit_price": Decimal("120.00"),
                }
            ],
        )

    def test_purchasing_manager_can_confirm_draft_order(self):
        self.client.force_login(self.purchasing_manager)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-confirm",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CONFIRMED,
        )

    def test_warehouse_employee_cannot_confirm_order(self):
        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-confirm",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.DRAFT,
        )

    def test_warehouse_employee_can_receive_confirmed_order(self):
        confirm_purchase_order(order_id=self.order.pk)

        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-receive",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.RECEIVED,
        )

        stock = Stock.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(
            stock.quantity,
            7,
        )

        movement = StockMovement.objects.get(
            purchase_order_item__purchase_order=self.order
        )

        self.assertEqual(
            movement.movement_type,
            StockMovement.MovementType.PURCHASE_RECEIPT,
        )

        self.assertEqual(
            movement.quantity,
            7,
        )

        self.assertEqual(
            movement.performed_by,
            self.warehouse_employee,
        )

    def test_purchasing_manager_cannot_receive_order(self):
        confirm_purchase_order(order_id=self.order.pk)

        self.client.force_login(self.purchasing_manager)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-receive",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CONFIRMED,
        )

        self.assertFalse(
            Stock.objects.filter(
                product=self.product,
                warehouse=self.warehouse,
            ).exists()
        )

    def test_purchasing_manager_can_cancel_confirmed_order(self):
        confirm_purchase_order(order_id=self.order.pk)

        self.client.force_login(self.purchasing_manager)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-cancel",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CANCELLED,
        )

    def test_warehouse_employee_cannot_cancel_order(self):
        confirm_purchase_order(order_id=self.order.pk)

        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "purchasing_web:purchase-order-cancel",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CONFIRMED,
        )
