from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Warehouse
from partners.models import Customer
from sales.models import SalesOrder


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

        self.warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
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

        SalesOrder.objects.create(
            order_number="SO-TEST-DRAFT",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
            status=SalesOrder.Status.DRAFT,
        )

        SalesOrder.objects.create(
            order_number="SO-TEST-SHIPPED",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.user,
            status=SalesOrder.Status.SHIPPED,
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
