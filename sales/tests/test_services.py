from django.contrib.auth import get_user_model
from django.test import TestCase

from catalog.models import Category, Manufacturer, Product
from inventory.models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)
from partners.models import Customer
from sales.exceptions import (
    InsufficientStock,
    InvalidSalesOrderStatus,
)
from sales.models import SalesOrder, SalesOrderItem
from sales.services import (
    cancel_sales_order,
    confirm_sales_order,
    ship_sales_order,
    start_processing_sales_order,
)


User = get_user_model()


class SalesOrderServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="sales@example.com",
            password="test12345",
        )

        self.category = Category.objects.create(
            name="Brake System",
            slug="brake-system",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Brembo",
        )

        self.product = Product.objects.create(
            sku="BP-001",
            name="Ceramic Brake Pads",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price="100.00",
        )

        self.customer = Customer.objects.create(
            name="Test Auto Service",
        )

        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=50,
            reorder_level=10,
        )

        self.order = SalesOrder.objects.create(
            order_number="SO-TEST-001",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
        )

        self.item = SalesOrderItem.objects.create(
            sales_order=self.order,
            product=self.product,
            quantity=5,
            unit_price="100.00",
        )

    def test_confirm_sales_order_creates_reservation(self):
        confirm_sales_order(
            order_id=self.order.id,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.CONFIRMED,
        )

        self.assertEqual(
            self.stock.quantity,
            50,
        )

        reservation = StockReservation.objects.get(
            sales_order_item=self.item,
        )

        self.assertEqual(
            reservation.status,
            StockReservation.Status.ACTIVE,
        )

        self.assertEqual(
            reservation.quantity,
            5,
        )

    def test_cancel_confirmed_order_releases_reservation(self):
        confirm_sales_order(
            order_id=self.order.id,
        )

        cancel_sales_order(
            order_id=self.order.id,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        reservation = StockReservation.objects.get(
            sales_order_item=self.item,
        )
        reservation.refresh_from_db()

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.CANCELLED,
        )

        self.assertEqual(
            reservation.status,
            StockReservation.Status.RELEASED,
        )

        self.assertEqual(
            self.stock.quantity,
            50,
        )

    def test_ship_sales_order_decreases_stock_and_creates_movement(self):
        confirm_sales_order(
            order_id=self.order.id,
        )

        start_processing_sales_order(
            order_id=self.order.id,
        )

        ship_sales_order(
            order_id=self.order.id,
            performed_by=self.user,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        reservation = StockReservation.objects.get(
            sales_order_item=self.item,
        )
        reservation.refresh_from_db()

        movement = StockMovement.objects.get(
            sales_order_item=self.item,
            movement_type=StockMovement.MovementType.SALES_SHIPMENT,
        )

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.SHIPPED,
        )

        self.assertEqual(
            self.stock.quantity,
            45,
        )

        self.assertEqual(
            reservation.status,
            StockReservation.Status.CONSUMED,
        )

        self.assertEqual(
            movement.quantity,
            -5,
        )

        self.assertEqual(
            movement.performed_by,
            self.user,
        )

    def test_confirm_sales_order_fails_when_stock_is_insufficient(self):
        self.item.quantity = 60
        self.item.save(update_fields=("quantity",))

        with self.assertRaises(InsufficientStock):
            confirm_sales_order(
                order_id=self.order.id,
            )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        self.assertEqual(
            self.order.status,
            SalesOrder.Status.DRAFT,
        )

        self.assertEqual(
            self.stock.quantity,
            50,
        )

        self.assertFalse(
            StockReservation.objects.filter(
                sales_order_item=self.item,
            ).exists()
        )

    def test_shipped_sales_order_cannot_be_shipped_again(self):
        confirm_sales_order(
            order_id=self.order.id,
        )

        start_processing_sales_order(
            order_id=self.order.id,
        )

        ship_sales_order(
            order_id=self.order.id,
            performed_by=self.user,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            45,
        )

        with self.assertRaises(InvalidSalesOrderStatus):
            ship_sales_order(
                order_id=self.order.id,
                performed_by=self.user,
            )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            45,
        )

        self.assertEqual(
            StockMovement.objects.filter(
                sales_order_item=self.item,
                movement_type=StockMovement.MovementType.SALES_SHIPMENT,
            ).count(),
            1,
        )
