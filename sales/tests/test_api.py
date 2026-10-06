from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rest_framework.test import APITestCase

from accounts.services import setup_roles
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
