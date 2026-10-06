from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Stock, StockMovement, Warehouse


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


class StockMovementAPITests(APITestCase):
    def setUp(self):
        setup_roles()

        warehouse_group = Group.objects.get(name="Warehouse Employee")

        sales_group = Group.objects.get(name="Sales Manager")

        self.warehouse_user = User.objects.create_user(
            email="warehouse-api@example.com",
            password="test12345",
        )
        self.warehouse_user.groups.add(warehouse_group)

        self.sales_user = User.objects.create_user(
            email="sales-api@example.com",
            password="test12345",
        )
        self.sales_user.groups.add(sales_group)

        category = Category.objects.create(
            name="Movement Category",
            slug="movement-category",
        )

        manufacturer = Manufacturer.objects.create(
            name="Movement Manufacturer",
        )

        self.product = Product.objects.create(
            sku="MOVE-001",
            name="Movement Product",
            category=category,
            manufacturer=manufacturer,
            sale_price="100.00",
        )

        self.warehouse = Warehouse.objects.create(
            name="Movement Warehouse",
            code="MOVE",
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=50,
            reorder_level=10,
        )

        StockMovement.objects.create(
            stock=self.stock,
            movement_type=(StockMovement.MovementType.SALES_SHIPMENT),
            quantity=-5,
            performed_by=self.warehouse_user,
        )

        StockMovement.objects.create(
            stock=self.stock,
            movement_type=(StockMovement.MovementType.ADJUSTMENT_IN),
            quantity=3,
            reason="Inventory correction",
            performed_by=self.warehouse_user,
        )

    def test_warehouse_employee_can_view_stock_movements(self):
        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.get("/api/stock-movements/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_sales_manager_cannot_view_stock_movements(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.get("/api/stock-movements/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_stock_movement_endpoint_is_read_only(self):
        superuser = User.objects.create_superuser(
            email="admin-api@example.com",
            password="test12345",
        )

        self.client.force_authenticate(user=superuser)

        payload = {
            "stock": self.stock.id,
            "movement_type": (StockMovement.MovementType.ADJUSTMENT_IN),
            "quantity": 10,
            "reason": "Should not be created via API",
        }

        response = self.client.post(
            "/api/stock-movements/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertEqual(
            StockMovement.objects.count(),
            2,
        )

    def test_stock_movement_filter_by_movement_type(self):
        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.get("/api/stock-movements/?movement_type=SALES_SHIPMENT")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        self.assertEqual(
            response.data["results"][0]["movement_type"],
            StockMovement.MovementType.SALES_SHIPMENT,
        )
