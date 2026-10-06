from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import (
    Stock,
    StockReservation,
    Warehouse,
)
from partners.models import Customer
from sales.models import SalesOrder, SalesOrderItem


User = get_user_model()


class SalesOrderFilterTests(APITestCase):
    def setUp(self):
        setup_roles()

        sales_group = Group.objects.get(name="Sales Manager")

        self.user = User.objects.create_user(
            email="sales@example.com",
            password="test12345",
        )
        self.user.groups.add(sales_group)

        self.client.force_authenticate(user=self.user)

        self.customer = Customer.objects.create(
            name="Test Customer",
        )

        self.second_customer = Customer.objects.create(
            name="Second Customer",
        )

        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
        )

        self.second_warehouse = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="SECONDARY",
        )

        self.category = Category.objects.create(
            name="Brake System",
            slug="brake-system",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Test Manufacturer",
        )

        self.product = Product.objects.create(
            sku="BP-001",
            name="Brake Pads",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price="100.00",
        )

        self.second_product = Product.objects.create(
            sku="BP-002",
            name="Brake Discs",
            category=self.category,
            manufacturer=self.manufacturer,
            sale_price="150.00",
        )

        self.draft_order = SalesOrder.objects.create(
            order_number="SO-TEST-DRAFT",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
            status=SalesOrder.Status.DRAFT,
        )

        SalesOrderItem.objects.create(
            sales_order=self.draft_order,
            product=self.product,
            quantity=2,
            unit_price="100.00",
        )

        self.shipped_order = SalesOrder.objects.create(
            order_number="SO-TEST-SHIPPED",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
            status=SalesOrder.Status.SHIPPED,
        )

        SalesOrderItem.objects.create(
            sales_order=self.shipped_order,
            product=self.product,
            quantity=1,
            unit_price="100.00",
        )

    def test_sales_order_filter_by_status(self):
        response = self.client.get("/api/sales-orders/?status=SHIPPED")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["status"],
            SalesOrder.Status.SHIPPED,
        )

    def test_sales_order_list_does_not_scale_queries_with_items(self):
        for index in range(5):
            SalesOrder.objects.create(
                order_number=f"SO-TEST-{index}",
                customer=self.customer,
                warehouse=self.warehouse,
                created_by=self.user,
                status=SalesOrder.Status.DRAFT,
            )

        with CaptureQueriesContext(connection) as context:
            response = self.client.get("/api/sales-orders/")

        self.assertEqual(
            response.status_code,
            200,
        )

        query_count = len(context)

        self.assertLess(
            query_count,
            7,
        )

    def test_order_number_is_generated_by_server(self):
        payload = {
            "order_number": "HACKED-123",
            "customer": self.customer.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 2,
                    "unit_price": "100.00",
                }
            ],
        }

        response = self.client.post(
            "/api/sales-orders/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertRegex(
            response.data["order_number"],
            r"^SO-\d{4}-\d{6}$",
        )

        self.assertNotEqual(
            response.data["order_number"],
            "HACKED-123",
        )

    def test_draft_sales_order_can_be_updated(self):
        payload = {
            "customer": self.second_customer.id,
            "warehouse": self.second_warehouse.id,
        }

        response = self.client.patch(
            f"/api/sales-orders/{self.draft_order.id}/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.draft_order.refresh_from_db()

        self.assertEqual(
            self.draft_order.customer,
            self.second_customer,
        )

        self.assertEqual(
            self.draft_order.warehouse,
            self.second_warehouse,
        )

    def test_draft_sales_order_items_can_be_replaced(self):
        payload = {
            "items": [
                {
                    "product": self.second_product.id,
                    "quantity": 4,
                    "unit_price": "150.00",
                }
            ]
        }

        response = self.client.patch(
            f"/api/sales-orders/{self.draft_order.id}/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            self.draft_order.items.count(),
            1,
        )

        item = self.draft_order.items.get()

        self.assertEqual(
            item.product,
            self.second_product,
        )

        self.assertEqual(
            item.quantity,
            4,
        )

        self.assertEqual(
            str(item.unit_price),
            "150.00",
        )

    def test_non_draft_sales_order_cannot_be_updated(self):
        payload = {
            "customer": self.second_customer.id,
        }

        response = self.client.patch(
            f"/api/sales-orders/{self.shipped_order.id}/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.shipped_order.refresh_from_db()

        self.assertEqual(
            self.shipped_order.customer,
            self.customer,
        )

    def test_sales_order_rejects_zero_item_quantity(self):
        payload = {
            "customer": self.customer.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 0,
                    "unit_price": "100.00",
                }
            ],
        }

        response = self.client.post(
            "/api/sales-orders/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_sales_order_rejects_duplicate_products(self):
        payload = {
            "customer": self.customer.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 1,
                    "unit_price": "100.00",
                },
                {
                    "product": self.product.id,
                    "quantity": 2,
                    "unit_price": "100.00",
                },
            ],
        }

        response = self.client.post(
            "/api/sales-orders/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_sales_order_cannot_be_deleted(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="test12345",
        )

        self.client.force_authenticate(user=superuser)

        response = self.client.delete(f"/api/sales-orders/{self.draft_order.id}/")

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertTrue(SalesOrder.objects.filter(id=self.draft_order.id).exists())


class SalesOrderActionPermissionTests(APITestCase):
    def setUp(self):
        setup_roles()

        sales_group = Group.objects.get(name="Sales Manager")

        warehouse_group = Group.objects.get(name="Warehouse Employee")

        self.sales_user = User.objects.create_user(
            email="sales-actions@example.com",
            password="test12345",
        )
        self.sales_user.groups.add(sales_group)

        self.warehouse_user = User.objects.create_user(
            email="warehouse-actions@example.com",
            password="test12345",
        )
        self.warehouse_user.groups.add(warehouse_group)

        self.customer = Customer.objects.create(
            name="Action Customer",
        )

        self.warehouse = Warehouse.objects.create(
            name="Action Warehouse",
            code="ACTION",
        )

        category = Category.objects.create(
            name="Action Category",
            slug="action-category",
        )

        manufacturer = Manufacturer.objects.create(
            name="Action Manufacturer",
        )

        self.product = Product.objects.create(
            sku="ACTION-001",
            name="Action Product",
            category=category,
            manufacturer=manufacturer,
            sale_price="100.00",
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=50,
            reorder_level=10,
        )

    def create_order(self, status):
        order = SalesOrder.objects.create(
            order_number=f"SO-ACTION-{status}",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.sales_user,
            status=status,
        )

        item = SalesOrderItem.objects.create(
            sales_order=order,
            product=self.product,
            quantity=5,
            unit_price="100.00",
        )

        return order, item

    def test_sales_manager_can_confirm_sales_order(self):
        order, _ = self.create_order(SalesOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/confirm/")

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            SalesOrder.Status.CONFIRMED,
        )

    def test_warehouse_employee_cannot_confirm_sales_order(self):
        order, _ = self.create_order(SalesOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/confirm/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_sales_manager_cannot_start_processing_sales_order(self):
        order, _ = self.create_order(SalesOrder.Status.CONFIRMED)

        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/start-processing/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_warehouse_employee_can_start_processing_sales_order(self):
        order, _ = self.create_order(SalesOrder.Status.CONFIRMED)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/start-processing/")

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            SalesOrder.Status.PROCESSING,
        )

    def test_warehouse_employee_cannot_cancel_sales_order(self):
        order, _ = self.create_order(SalesOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/cancel/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_sales_manager_cannot_ship_sales_order(self):
        order, item = self.create_order(SalesOrder.Status.PROCESSING)

        StockReservation.objects.create(
            sales_order_item=item,
            stock=self.stock,
            quantity=5,
            status=StockReservation.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/ship/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_warehouse_employee_can_ship_sales_order(self):
        order, item = self.create_order(SalesOrder.Status.PROCESSING)

        reservation = StockReservation.objects.create(
            sales_order_item=item,
            stock=self.stock,
            quantity=5,
            status=StockReservation.Status.ACTIVE,
        )

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/sales-orders/{order.id}/ship/")

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()
        self.stock.refresh_from_db()
        reservation.refresh_from_db()

        self.assertEqual(
            order.status,
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
