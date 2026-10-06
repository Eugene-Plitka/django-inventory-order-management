from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rest_framework.test import APITestCase

from accounts.services import setup_roles
from catalog.models import Category, Manufacturer, Product
from inventory.models import Stock, Warehouse
from partners.models import Supplier
from purchasing.models import PurchaseOrder, PurchaseOrderItem


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

        self.second_supplier = Supplier.objects.create(
            name="Second Supplier",
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

        self.draft_order = PurchaseOrder.objects.create(
            order_number="PO-TEST-DRAFT",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
            status=PurchaseOrder.Status.DRAFT,
        )

        PurchaseOrderItem.objects.create(
            purchase_order=self.draft_order,
            product=self.product,
            quantity=4,
            unit_price="60.00",
        )

        self.confirmed_order = PurchaseOrder.objects.create(
            order_number="PO-TEST-CONFIRMED",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.user,
            status=PurchaseOrder.Status.CONFIRMED,
        )

        PurchaseOrderItem.objects.create(
            purchase_order=self.confirmed_order,
            product=self.product,
            quantity=3,
            unit_price="60.00",
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

    def test_draft_purchase_order_can_be_updated(self):
        payload = {
            "supplier": self.second_supplier.id,
            "warehouse": self.second_warehouse.id,
        }

        response = self.client.patch(
            f"/api/purchase-orders/{self.draft_order.id}/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.draft_order.refresh_from_db()

        self.assertEqual(
            self.draft_order.supplier,
            self.second_supplier,
        )

        self.assertEqual(
            self.draft_order.warehouse,
            self.second_warehouse,
        )

    def test_draft_purchase_order_items_can_be_replaced(self):
        payload = {
            "items": [
                {
                    "product": self.second_product.id,
                    "quantity": 8,
                    "unit_price": "75.00",
                }
            ]
        }

        response = self.client.patch(
            f"/api/purchase-orders/{self.draft_order.id}/",
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
            8,
        )

        self.assertEqual(
            str(item.unit_price),
            "75.00",
        )

    def test_non_draft_purchase_order_cannot_be_updated(self):
        payload = {
            "supplier": self.second_supplier.id,
        }

        response = self.client.patch(
            f"/api/purchase-orders/{self.confirmed_order.id}/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.confirmed_order.refresh_from_db()

        self.assertEqual(
            self.confirmed_order.supplier,
            self.supplier,
        )

    def test_purchase_order_rejects_zero_item_quantity(self):
        payload = {
            "supplier": self.supplier.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 0,
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
            400,
        )

    def test_purchase_order_rejects_duplicate_products(self):
        payload = {
            "supplier": self.supplier.id,
            "warehouse": self.warehouse.id,
            "items": [
                {
                    "product": self.product.id,
                    "quantity": 2,
                    "unit_price": "60.00",
                },
                {
                    "product": self.product.id,
                    "quantity": 3,
                    "unit_price": "65.00",
                },
            ],
        }

        response = self.client.post(
            "/api/purchase-orders/",
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            400,
        )

    def test_purchase_order_cannot_be_deleted(self):
        superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="test12345",
        )

        self.client.force_authenticate(user=superuser)

        response = self.client.delete(f"/api/purchase-orders/{self.draft_order.id}/")

        self.assertEqual(
            response.status_code,
            405,
        )

        self.assertTrue(PurchaseOrder.objects.filter(id=self.draft_order.id).exists())


class PurchaseOrderActionPermissionTests(APITestCase):
    def setUp(self):
        setup_roles()

        purchasing_group = Group.objects.get(name="Purchasing Manager")

        warehouse_group = Group.objects.get(name="Warehouse Employee")

        self.purchasing_user = User.objects.create_user(
            email="purchasing-actions@example.com",
            password="test12345",
        )
        self.purchasing_user.groups.add(purchasing_group)

        self.warehouse_user = User.objects.create_user(
            email="warehouse-purchasing-actions@example.com",
            password="test12345",
        )
        self.warehouse_user.groups.add(warehouse_group)

        self.supplier = Supplier.objects.create(
            name="Action Supplier",
        )

        self.warehouse = Warehouse.objects.create(
            name="Purchase Action Warehouse",
            code="PUR-ACTION",
        )

        category = Category.objects.create(
            name="Purchase Action Category",
            slug="purchase-action-category",
        )

        manufacturer = Manufacturer.objects.create(
            name="Purchase Action Manufacturer",
        )

        self.product = Product.objects.create(
            sku="PUR-ACTION-001",
            name="Purchase Action Product",
            category=category,
            manufacturer=manufacturer,
            sale_price="100.00",
        )

    def create_order(self, status):
        order = PurchaseOrder.objects.create(
            order_number=f"PO-ACTION-{status}",
            supplier=self.supplier,
            warehouse=self.warehouse,
            created_by=self.purchasing_user,
            status=status,
        )

        PurchaseOrderItem.objects.create(
            purchase_order=order,
            product=self.product,
            quantity=5,
            unit_price="60.00",
        )

        return order

    def test_purchasing_manager_can_confirm_purchase_order(self):
        order = self.create_order(PurchaseOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.post(f"/api/purchase-orders/{order.id}/confirm/")

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            PurchaseOrder.Status.CONFIRMED,
        )

    def test_warehouse_employee_cannot_confirm_purchase_order(self):
        order = self.create_order(PurchaseOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/purchase-orders/{order.id}/confirm/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_purchasing_manager_cannot_receive_purchase_order(self):
        order = self.create_order(PurchaseOrder.Status.CONFIRMED)

        self.client.force_authenticate(user=self.purchasing_user)

        response = self.client.post(f"/api/purchase-orders/{order.id}/receive/")

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_warehouse_employee_can_receive_purchase_order(self):
        order = self.create_order(PurchaseOrder.Status.CONFIRMED)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/purchase-orders/{order.id}/receive/")

        self.assertEqual(
            response.status_code,
            200,
        )

        order.refresh_from_db()

        self.assertEqual(
            order.status,
            PurchaseOrder.Status.RECEIVED,
        )

        stock = Stock.objects.get(
            product=self.product,
            warehouse=self.warehouse,
        )

        self.assertEqual(
            stock.quantity,
            5,
        )

    def test_warehouse_employee_cannot_cancel_purchase_order(self):
        order = self.create_order(PurchaseOrder.Status.DRAFT)

        self.client.force_authenticate(user=self.warehouse_user)

        response = self.client.post(f"/api/purchase-orders/{order.id}/cancel/")

        self.assertEqual(
            response.status_code,
            403,
        )
