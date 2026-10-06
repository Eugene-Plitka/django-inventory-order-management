from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Stock, Warehouse


User = get_user_model()


class StockFilterTests(APITestCase):
    def setUp(self):
        setup_roles()

        sales_group = Group.objects.get(name="Sales Manager")

        self.user = User.objects.create_user(
            email="sales@example.com",
            password="test12345",
        )
        self.user.groups.add(sales_group)

        self.client.force_authenticate(user=self.user)

        category = Category.objects.create(
            name="Brake System",
            slug="brake-system",
        )

        manufacturer = Manufacturer.objects.create(
            name="Brembo",
        )

        self.product = Product.objects.create(
            sku="BP-001",
            name="Ceramic Brake Pads",
            category=category,
            manufacturer=manufacturer,
            sale_price="100.00",
        )

        self.main_warehouse = Warehouse.objects.create(
            name="Main Warehouse",
            code="MAIN",
        )

        self.secondary_warehouse = Warehouse.objects.create(
            name="Secondary Warehouse",
            code="SECONDARY",
        )

        Stock.objects.create(
            product=self.product,
            warehouse=self.main_warehouse,
            quantity=50,
            reorder_level=10,
        )

        Stock.objects.create(
            product=self.product,
            warehouse=self.secondary_warehouse,
            quantity=20,
            reorder_level=5,
        )

    def test_stock_filter_by_warehouse(self):
        response = self.client.get(f"/api/stocks/?warehouse={self.main_warehouse.id}")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["warehouse"],
            self.main_warehouse.id,
        )
