from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)
from partners.models import Customer
from sales.models import SalesOrder, SalesOrderItem


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

        self.main_stock = Stock.objects.create(
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

        self.customer = Customer.objects.create(
            name="Available Stock Customer",
        )

        self.sales_order = SalesOrder.objects.create(
            order_number="SO-AVAILABLE-001",
            customer=self.customer,
            warehouse=self.main_warehouse,
            created_by=self.user,
        )

        self.sales_order_item = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=15,
            unit_price="100.00",
        )

        StockReservation.objects.create(
            sales_order_item=self.sales_order_item,
            stock=self.main_stock,
            quantity=15,
            status=StockReservation.Status.ACTIVE,
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

    def test_stock_returns_reserved_and_available_quantity(self):
        response = self.client.get(f"/api/stocks/{self.main_stock.id}/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["quantity"],
            50,
        )

        self.assertEqual(
            response.data["reserved_quantity"],
            15,
        )

        self.assertEqual(
            response.data["available_quantity"],
            35,
        )

    def test_released_and_consumed_reservations_do_not_reduce_available_quantity(self):
        StockReservation.objects.create(
            sales_order_item=self.sales_order_item,
            stock=self.main_stock,
            quantity=7,
            status=StockReservation.Status.RELEASED,
        )

        StockReservation.objects.create(
            sales_order_item=self.sales_order_item,
            stock=self.main_stock,
            quantity=4,
            status=StockReservation.Status.CONSUMED,
        )

        response = self.client.get(f"/api/stocks/{self.main_stock.id}/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["quantity"],
            50,
        )

        self.assertEqual(
            response.data["reserved_quantity"],
            15,
        )

        self.assertEqual(
            response.data["available_quantity"],
            35,
        )

    def test_stock_filter_by_low_stock(self):
        self.main_stock.quantity = 20
        self.main_stock.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

        response = self.client.get("/api/stocks/?low_stock=true")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        stock = response.data["results"][0]

        self.assertEqual(
            stock["id"],
            self.main_stock.id,
        )

        self.assertEqual(
            stock["quantity"],
            20,
        )

        self.assertEqual(
            stock["reserved_quantity"],
            15,
        )

        self.assertEqual(
            stock["available_quantity"],
            5,
        )

        self.assertEqual(
            stock["reorder_level"],
            10,
        )

    def test_stock_filter_by_not_low_stock(self):
        self.main_stock.quantity = 20
        self.main_stock.save(
            update_fields=(
                "quantity",
                "updated_at",
            )
        )

        response = self.client.get("/api/stocks/?low_stock=false")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            1,
        )

        stock = response.data["results"][0]

        self.assertEqual(
            stock["warehouse"],
            self.secondary_warehouse.id,
        )

        self.assertEqual(
            stock["available_quantity"],
            20,
        )

        self.assertEqual(
            stock["reorder_level"],
            5,
        )

    def test_stock_filter_rejects_invalid_low_stock_value(self):
        response = self.client.get("/api/stocks/?low_stock=abc")

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "low_stock",
            response.data,
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


class StockReservationAPITests(APITestCase):
    def setUp(self):
        setup_roles()

        warehouse_group = Group.objects.get(name="Warehouse Employee")

        sales_group = Group.objects.get(name="Sales Manager")

        self.warehouse_user = User.objects.create_user(
            email="warehouse-reservation@example.com",
            password="test12345",
        )
        self.warehouse_user.groups.add(warehouse_group)

        self.sales_user = User.objects.create_user(
            email="sales-reservation@example.com",
            password="test12345",
        )
        self.sales_user.groups.add(sales_group)

        category = Category.objects.create(
            name="Reservation Category",
            slug="reservation-category",
        )

        manufacturer = Manufacturer.objects.create(
            name="Reservation Manufacturer",
        )

        self.product = Product.objects.create(
            sku="RES-001",
            name="Reservation Product",
            category=category,
            manufacturer=manufacturer,
            sale_price="100.00",
        )

        self.customer = Customer.objects.create(
            name="Reservation Customer",
        )

        self.warehouse = Warehouse.objects.create(
            name="Reservation Warehouse",
            code="RESERVE",
        )

        self.stock = Stock.objects.create(
            product=self.product,
            warehouse=self.warehouse,
            quantity=50,
            reorder_level=10,
        )

        self.sales_order = SalesOrder.objects.create(
            order_number="SO-RES-001",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.sales_user,
        )

        self.sales_order_item = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=5,
            unit_price="100.00",
        )

        StockReservation.objects.create(
            sales_order_item=self.sales_order_item,
            stock=self.stock,
            quantity=5,
            status=StockReservation.Status.ACTIVE,
        )

        StockReservation.objects.create(
            sales_order_item=self.sales_order_item,
            stock=self.stock,
            quantity=2,
            status=StockReservation.Status.RELEASED,
        )

    def test_warehouse_employee_can_view_stock_reservations(self):
        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.get("/api/stock-reservations/")

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.data["count"],
            2,
        )

    def test_sales_manager_cannot_view_stock_reservations(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.get("/api/stock-reservations/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_stock_reservation_endpoint_is_read_only(self):
        superuser = User.objects.create_superuser(
            email="admin-reservation@example.com",
            password="test12345",
        )

        self.client.force_authenticate(user=superuser)

        payload = {
            "sales_order_item": self.sales_order_item.id,
            "stock": self.stock.id,
            "quantity": 10,
            "status": StockReservation.Status.ACTIVE,
        }

        response = self.client.post(
            "/api/stock-reservations/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertEqual(
            StockReservation.objects.count(),
            2,
        )

    def test_stock_reservation_filter_by_status(self):
        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.get("/api/stock-reservations/?status=ACTIVE")

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
            StockReservation.Status.ACTIVE,
        )
