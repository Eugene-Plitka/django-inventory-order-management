from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Stock, Warehouse
from partners.models import Customer, Supplier
from purchasing.models import PurchaseOrder, PurchaseOrderItem
from sales.models import SalesOrder, SalesOrderItem
from sales.services import confirm_sales_order, start_processing_sales_order


User = get_user_model()


class APIPermissionTests(APITestCase):
    def setUp(self):
        setup_roles()

        self.sales_group = Group.objects.get(name="Sales Manager")
        self.purchasing_group = Group.objects.get(name="Purchasing Manager")
        self.warehouse_group = Group.objects.get(name="Warehouse Employee")
        self.admin_group = Group.objects.get(name="Administrator")

        self.sales_user = User.objects.create_user(
            email="sales@example.com",
            password="test12345",
        )
        self.sales_user.groups.add(self.sales_group)

        self.purchasing_user = User.objects.create_user(
            email="purchasing@example.com",
            password="test12345",
        )
        self.purchasing_user.groups.add(self.purchasing_group)

        self.warehouse_user = User.objects.create_user(
            email="warehouse@example.com",
            password="test12345",
        )
        self.warehouse_user.groups.add(self.warehouse_group)

        self.admin_user = User.objects.create_user(
            email="admin@example.com",
            password="test12345",
        )
        self.admin_user.groups.add(self.admin_group)

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
            name="Test Customer",
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
            quantity=50,
            reorder_level=10,
        )

        self.sales_order = SalesOrder.objects.create(
            order_number="SO-TEST-001",
            customer=self.customer,
            warehouse=self.warehouse,
            created_by=self.sales_user,
        )

        self.sales_item = SalesOrderItem.objects.create(
            sales_order=self.sales_order,
            product=self.product,
            quantity=5,
            unit_price="100.00",
        )

        confirm_sales_order(
            order_id=self.sales_order.id,
        )

        start_processing_sales_order(
            order_id=self.sales_order.id,
        )

        self.purchase_order = PurchaseOrder.objects.create(
            order_number="PO-TEST-001",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.purchasing_user,
        )

        self.purchase_item = PurchaseOrderItem.objects.create(
            purchase_order=self.purchase_order,
            product=self.product,
            quantity=10,
            unit_price="60.00",
        )

    def test_sales_manager_cannot_ship_sales_order(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(f"/api/sales-orders/{self.sales_order.id}/ship/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_warehouse_employee_cannot_confirm_sales_order(self):
        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/sales-orders/{self.sales_order.id}/confirm/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_purchasing_manager_cannot_receive_purchase_order(self):
        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.post(
            f"/api/purchase-orders/{self.purchase_order.id}/receive/"
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_administrator_can_adjust_stock(self):
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            f"/api/stocks/{self.stock.id}/adjust/",
            {
                "quantity": 5,
                "reason": "Inventory correction",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.stock.refresh_from_db()

        self.assertEqual(
            self.stock.quantity,
            55,
        )

    def test_sales_manager_can_view_products(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.get("/api/products/")

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_sales_manager_cannot_create_product(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(
            "/api/products/",
            {
                "sku": "TEST-999",
                "name": "Forbidden Product",
                "description": "",
                "category": self.category.id,
                "manufacturer": self.manufacturer.id,
                "sale_price": "50.00",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_sales_manager_can_create_customer(self):
        self.client.force_authenticate(user=self.sales_user)

        response = self.client.post(
            "/api/customers/",
            {
                "name": "New Customer",
                "contact_person": "John Doe",
                "email": "customer@example.com",
                "phone": "+380000000000",
                "address": "Odesa",
                "tax_id": "TEST-001",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            201,
        )

    def test_purchasing_manager_cannot_create_customer(self):
        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.post(
            "/api/customers/",
            {
                "name": "Forbidden Customer",
                "is_active": True,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            403,
        )
