from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Warehouse
from partners.models import Supplier


User = get_user_model()


class PurchaseOrderAPITests(APITestCase):
    def setUp(self):
        setup_roles()

        purchasing_group = Group.objects.get(name="Purchasing Manager")

        self.user = User.objects.create_user(
            email="purchasing@example.com",
            password="test12345",
        )
        self.user.groups.add(purchasing_group)

        self.client.force_authenticate(user=self.user)

        self.supplier = Supplier.objects.create(
            name="Test Supplier",
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

    def test_order_number_is_generated_by_server(self):
        payload = {
            "order_number": "HACKED-123",
            "supplier": self.supplier.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 4,
                    "unit_price": "60.00",
                }
            ],
        }

        response = self.client.post(
            "/api/purchase-orders/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

        self.assertRegex(
            response.data["order_number"],
            r"^PO-\d{4}-\d{6}$",
        )

        self.assertNotEqual(
            response.data["order_number"],
            "HACKED-123",
        )
