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
    StockReservation,
    Warehouse,
)
from partners.models import Customer
from sales.models import SalesOrder
from sales.services import (
    confirm_sales_order,
    create_sales_order,
    start_processing_sales_order,
)


class SalesOrderWebLifecycleTests(TestCase):
    def setUp(self):
        setup_roles()

        self.sales_manager = User.objects.create_user(
            email="sales-web@example.com",
            password="StrongPass123!",
        )

        self.sales_manager.groups.add(Group.objects.get(name="Sales Manager"))

        self.warehouse_employee = User.objects.create_user(
            email="warehouse-web@example.com",
            password="StrongPass123!",
        )

        self.warehouse_employee.groups.add(Group.objects.get(name="Warehouse Employee"))

        self.category = Category.objects.create(
            name="Brakes",
            slug="brakes",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Brembo",
        )

        self.product = Product.objects.create(
            sku="BP-WEB-001",
            name="Brake Pads",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price=Decimal("100.00"),
            is_active=True,
        )

        self.customer = Customer.objects.create(
            name="Web Test Customer",
            is_active=True,
        )

        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN-WEB",
            is_active=True,
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=20,
            reorder_level=5,
        )

        self.order = create_sales_order(
            created_by=self.sales_manager,
            customer=self.customer,
            warehouse=self.warehouse,
            items=[
                {
                    "product": self.product,
                    "quantity": 5,
                    "unit_price": Decimal("95.00"),
                }
            ],
        )

    def test_sales_manager_can_confirm_draft_order(self):
        self.client.force_login(self.sales_manager)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-confirm",
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
            SalesOrder.Status.CONFIRMED,
        )

        reservation = StockReservation.objects.get(
            sales_order_item__sales_order=self.order
        )

        self.assertEqual(
            reservation.status,
            StockReservation.Status.ACTIVE,
        )

        self.assertEqual(
            reservation.quantity,
            5,
        )

    def test_warehouse_employee_cannot_confirm_order(self):
        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-confirm",
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
            SalesOrder.Status.DRAFT,
        )

    def test_warehouse_employee_can_start_processing(self):
        confirm_sales_order(order_id=self.order.pk)

        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-start-processing",
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
            SalesOrder.Status.PROCESSING,
        )

    def test_sales_manager_cannot_start_processing(self):
        confirm_sales_order(order_id=self.order.pk)

        self.client.force_login(self.sales_manager)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-start-processing",
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
            SalesOrder.Status.CONFIRMED,
        )

    def test_warehouse_employee_can_ship_processing_order(self):
        confirm_sales_order(order_id=self.order.pk)

        start_processing_sales_order(order_id=self.order.pk)

        self.client.force_login(self.warehouse_employee)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-ship",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.SHIPPED,
        )

        self.assertEqual(
            self.stock.quantity,
            15,
        )

        reservation = StockReservation.objects.get(
            sales_order_item__sales_order=self.order
        )

        self.assertEqual(
            reservation.status,
            StockReservation.Status.CONSUMED,
        )

        movement = StockMovement.objects.get(sales_order_item__sales_order=self.order)

        self.assertEqual(
            movement.movement_type,
            StockMovement.MovementType.SALES_SHIPMENT,
        )

        self.assertEqual(
            movement.quantity,
            -5,
        )

        self.assertEqual(
            movement.performed_by,
            self.warehouse_employee,
        )

    def test_sales_manager_cannot_ship_order(self):
        confirm_sales_order(order_id=self.order.pk)

        start_processing_sales_order(order_id=self.order.pk)

        self.client.force_login(self.sales_manager)

        response = self.client.post(
            reverse(
                "sales_web:sales-order-ship",
                args=[self.order.pk],
            )
        )

        self.assertEqual(
            response.status_code,
            403,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.PROCESSING,
        )

        self.assertEqual(
            self.stock.quantity,
            20,
        )
