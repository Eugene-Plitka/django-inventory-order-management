from concurrent.futures import ThreadPoolExecutor

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase

from catalog.models import Category, Manufacturer, Product
from inventory.models import Stock, StockMovement, Warehouse
from partners.models import Supplier
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from purchasing.services import (
    InvalidPurchaseOrderStatus,
    cancel_purchase_order,
    confirm_purchase_order,
    receive_purchase_order,
)


User = get_user_model()


class PurchaseOrderServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="purchasing@example.com",
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

        self.supplier = Supplier.objects.create(
            name="Test Supplier",
        )

        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=20,
            reorder_level=10,
        )

        self.order = PurchaseOrder.objects.create(
            order_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
        )

        self.item = PurchaseOrderItem.objects.create(
            purchase_order=self.order,
            product=self.product,
            quantity=10,
            unit_price="60.00",
        )

    def test_confirm_purchase_order_changes_status(self):
        confirm_purchase_order(
            order_id=self.order.id,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CONFIRMED,
        )

        self.assertIsNotNone(
            self.order.confirmed_at,
        )

    def test_receive_purchase_order_increases_stock_and_creates_movement(self):
        confirm_purchase_order(
            order_id=self.order.id,
        )

        receive_purchase_order(
            order_id=self.order.id,
            performed_by=self.user,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        movement = StockMovement.objects.get(
            purchase_order_item=self.item,
            movement_type=StockMovement.MovementType.PURCHASE_RECEIPT,
        )

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.RECEIVED,
        )

        self.assertEqual(
            self.stock.quantity,
            30,
        )

        self.assertEqual(
            movement.quantity,
            10,
        )

        self.assertEqual(
            movement.performed_by,
            self.user,
        )

    def test_cancel_draft_purchase_order(self):
        cancel_purchase_order(
            order_id=self.order.id,
        )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CANCELLED,
        )

        self.assertIsNotNone(
            self.order.cancelled_at,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            20,
        )

    def test_cancel_confirmed_purchase_order(self):
        confirm_purchase_order(
            order_id=self.order.id,
        )

        cancel_purchase_order(
            order_id=self.order.id,
        )

        self.order.refresh_from_db()
        self.stock.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.CANCELLED,
        )

        self.assertEqual(
            self.stock.quantity,
            20,
        )

        self.assertFalse(
            StockMovement.objects.filter(
                purchase_order_item=self.item,
            ).exists()
        )

    def test_received_purchase_order_cannot_be_received_again(self):
        confirm_purchase_order(
            order_id=self.order.id,
        )

        receive_purchase_order(
            order_id=self.order.id,
            performed_by=self.user,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            30,
        )

        with self.assertRaises(InvalidPurchaseOrderStatus):
            receive_purchase_order(
                order_id=self.order.id,
                performed_by=self.user,
            )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            30,
        )

        self.assertEqual(
            StockMovement.objects.filter(
                purchase_order_item=self.item,
                movement_type=StockMovement.MovementType.PURCHASE_RECEIPT,
            ).count(),
            1,
        )

    def test_received_purchase_order_cannot_be_cancelled(self):
        confirm_purchase_order(
            order_id=self.order.id,
        )

        receive_purchase_order(
            order_id=self.order.id,
            performed_by=self.user,
        )

        with self.assertRaises(InvalidPurchaseOrderStatus):
            cancel_purchase_order(
                order_id=self.order.id,
            )

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.status,
            PurchaseOrder.Status.RECEIVED,
        )


class PurchaseOrderConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.user = User.objects.create_user(
            email="concurrency@example.com",
            password="test12345",
        )

        self.category = Category.objects.create(
            name="Concurrency Category",
            slug="concurrency-category",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Concurrency Manufacturer",
        )

        self.product = Product.objects.create(
            sku="CONCURRENT-001",
            name="Concurrent Product",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price="100.00",
        )

        self.supplier = Supplier.objects.create(
            name="Concurrency Supplier",
        )

        self.warehouse = Warehouse.objects.create(
            name="Concurrency Warehouse",
            code="CONCURRENT",
        )

        self.first_order = PurchaseOrder.objects.create(
            order_number="PO-CONCURRENT-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
        )

        self.first_item = PurchaseOrderItem.objects.create(
            purchase_order=self.first_order,
            product=self.product,
            quantity=10,
            unit_price="60.00",
        )

        self.second_order = PurchaseOrder.objects.create(
            order_number="PO-CONCURRENT-002",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
        )

        self.second_item = PurchaseOrderItem.objects.create(
            purchase_order=self.second_order,
            product=self.product,
            quantity=15,
            unit_price="60.00",
        )

        confirm_purchase_order(
            order_id=self.first_order.id,
        )

        confirm_purchase_order(
            order_id=self.second_order.id,
        )

        self.assertFalse(
            Stock.objects.filter(
                product=self.product,
                warehouse=self.warehouse,
            ).exists()
        )

    def receive_order(self, order_id):
        close_old_connections()

        try:
            receive_purchase_order(
                order_id=order_id,
                performed_by=self.user,
            )
        finally:
            close_old_connections()

    def test_concurrent_receive_creates_single_stock_and_preserves_quantity(
        self,
    ):
        with ThreadPoolExecutor(max_workers=2) as executor:
            first_future = executor.submit(
                self.receive_order,
                self.first_order.id,
            )

            second_future = executor.submit(
                self.receive_order,
                self.second_order.id,
            )

            first_future.result()
            second_future.result()

        stocks = Stock.objects.filter(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(
            stocks.count(),
            1,
        )

        stock = stocks.get()

        self.assertEqual(
            stock.quantity,
            25,
        )

        self.first_order.refresh_from_db()
        self.second_order.refresh_from_db()

        self.assertEqual(
            self.first_order.status,
            PurchaseOrder.Status.RECEIVED,
        )

        self.assertEqual(
            self.second_order.status,
            PurchaseOrder.Status.RECEIVED,
        )

        movements = StockMovement.objects.filter(
            stock=stock,
            movement_type=(StockMovement.MovementType.PURCHASE_RECEIPT),
        )

        self.assertEqual(
            movements.count(),
            2,
        )

        self.assertTrue(
            movements.filter(
                purchase_order_item=self.first_item,
                quantity=10,
            ).exists()
        )

        self.assertTrue(
            movements.filter(
                purchase_order_item=self.second_item,
                quantity=15,
            ).exists()
        )
