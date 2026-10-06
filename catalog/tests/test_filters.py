from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product


User = get_user_model()


class ProductFilterTests(APITestCase):
    def setUp(self):
        setup_roles()

        sales_group = Group.objects.get(name="Sales Manager")

        self.user = User.objects.create_user(
            email="sales@example.com",
            password="test12345",
        )
        self.user.groups.add(sales_group)

        self.client.force_authenticate(user=self.user)

        self.brake_category = Category.objects.create(
            name="Brake System",
            slug="brake-system",
        )

        self.engine_category = Category.objects.create(
            name="Engine",
            slug="engine",
        )

        self.manufacturer = Manufacturer.objects.create(
            name="Brembo",
        )

        self.brake_product = Product.objects.create(
            sku="BP-001",
            name="Ceramic Brake Pads",
            description="Front brake pads",
            category=self.brake_category,
            manufacturer=self.manufacturer,
            sale_price="100.00",
        )

        self.engine_product = Product.objects.create(
            sku="EN-001",
            name="Engine Filter",
            description="Engine oil filter",
            category=self.engine_category,
            manufacturer=self.manufacturer,
            sale_price="50.00",
        )

    def test_product_list_uses_pagination(self):
        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertIn(
            "count",
            response.data,
        )
        self.assertIn(
            "next",
            response.data,
        )
        self.assertIn(
            "previous",
            response.data,
        )
        self.assertIn(
            "results",
            response.data,
        )

    def test_product_search_by_name(self):
        response = self.client.get("/api/products/?search=brake")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["sku"],
            "BP-001",
        )

    def test_product_filter_by_category(self):
        response = self.client.get(f"/api/products/?category={self.engine_category.id}")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["sku"],
            "EN-001",
        )

    def test_product_ordering_by_sale_price_descending(self):
        response = self.client.get("/api/products/?ordering=-sale_price")

        self.assertEqual(
            response.status_code,
            200,
        )

        results = response.data["results"]

        self.assertEqual(
            results[0]["sku"],
            "BP-001",
        )

        self.assertEqual(
            results[1]["sku"],
            "EN-001",
        )
