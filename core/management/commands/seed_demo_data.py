from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import (
    models,
    transaction,
)
from django.utils import timezone

from catalog.models import (
    Category,
    Manufacturer,
    Product,
)
from core.models import SystemSettings
from inventory.models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)
from inventory.services import adjust_stock
from notifications.models import Notification
from partners.models import (
    Customer,
    Supplier,
)
from purchasing.models import PurchaseOrder
from purchasing.services import (
    cancel_purchase_order,
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
)
from sales.models import SalesOrder
from sales.services import (
    cancel_sales_order,
    confirm_sales_order,
    create_sales_order,
    ship_sales_order,
    start_processing_sales_order,
)


User = get_user_model()


CATEGORIES = [
    {
        "name": "Brake System",
        "slug": "brake-system",
        "description": ("Brake pads, discs and related braking components."),
    },
    {
        "name": "Filters",
        "slug": "filters",
        "description": ("Oil, air, fuel and cabin filtration components."),
    },
    {
        "name": "Ignition",
        "slug": "ignition",
        "description": ("Spark plugs, ignition coils and related components."),
    },
    {
        "name": "Engine Parts",
        "slug": "engine-parts",
        "description": ("Engine components, thermostats and internal parts."),
    },
    {
        "name": "Suspension",
        "slug": "suspension",
        "description": ("Shock absorbers, bearings and suspension components."),
    },
    {
        "name": "Belts & Timing",
        "slug": "belts-timing",
        "description": ("Timing belts, tensioners and auxiliary drive belts."),
    },
    {
        "name": "Electrical",
        "slug": "electrical",
        "description": ("Sensors and automotive electrical components."),
    },
    {
        "name": "Cooling System",
        "slug": "cooling-system",
        "description": ("Water pumps, thermostats and cooling components."),
    },
]


MANUFACTURERS = [
    {
        "name": "Brembo",
        "country": "Italy",
        "website": "https://www.brembo.com",
    },
    {
        "name": "Bosch",
        "country": "Germany",
        "website": "https://www.boschaftermarket.com",
    },
    {
        "name": "MANN-FILTER",
        "country": "Germany",
        "website": "https://www.mann-filter.com",
    },
    {
        "name": "MAHLE",
        "country": "Germany",
        "website": "https://www.mahle-aftermarket.com",
    },
    {
        "name": "SKF",
        "country": "Sweden",
        "website": "https://www.skf.com",
    },
    {
        "name": "SACHS",
        "country": "Germany",
        "website": "https://aftermarket.zf.com",
    },
    {
        "name": "NGK",
        "country": "Japan",
        "website": "https://www.ngkntk.com",
    },
    {
        "name": "DENSO",
        "country": "Japan",
        "website": "https://www.denso-am.eu",
    },
    {
        "name": "Gates",
        "country": "USA",
        "website": "https://www.gates.com",
    },
    {
        "name": "Continental",
        "country": "Germany",
        "website": "https://www.continental-aftermarket.com",
    },
]


PRODUCTS = [
    {
        "sku": "BRM-BP-001",
        "name": "Ceramic Front Brake Pad Set",
        "manufacturer": "Brembo",
        "category": "Brake System",
        "price": "68.90",
        "description": ("Premium ceramic front brake pad set for passenger vehicles."),
    },
    {
        "sku": "BRM-BP-002",
        "name": "Rear Brake Pad Set",
        "manufacturer": "Brembo",
        "category": "Brake System",
        "price": "54.50",
        "description": ("Rear axle brake pad set for everyday passenger vehicles."),
    },
    {
        "sku": "BRM-BD-001",
        "name": "Ventilated Front Brake Disc",
        "manufacturer": "Brembo",
        "category": "Brake System",
        "price": "92.00",
        "description": ("Ventilated front brake disc for high thermal performance."),
    },
    {
        "sku": "BRM-BD-002",
        "name": "Rear Brake Disc",
        "manufacturer": "Brembo",
        "category": "Brake System",
        "price": "71.00",
        "description": ("Standard rear brake disc for passenger vehicles."),
    },
    {
        "sku": "BOS-OF-001",
        "name": "Premium Oil Filter",
        "manufacturer": "Bosch",
        "category": "Filters",
        "price": "11.90",
        "description": ("Engine oil filter designed for reliable contaminant capture."),
    },
    {
        "sku": "BOS-AF-001",
        "name": "Engine Air Filter",
        "manufacturer": "Bosch",
        "category": "Filters",
        "price": "18.50",
        "description": ("Engine intake air filter for standard service intervals."),
    },
    {
        "sku": "BOS-FU-001",
        "name": "Fuel Filter",
        "manufacturer": "Bosch",
        "category": "Filters",
        "price": "24.90",
        "description": ("Fuel filtration component for modern fuel systems."),
    },
    {
        "sku": "BOS-OS-001",
        "name": "Oxygen Sensor",
        "manufacturer": "Bosch",
        "category": "Electrical",
        "price": "76.00",
        "description": ("Exhaust oxygen sensor for engine management systems."),
    },
    {
        "sku": "MANN-OF-001",
        "name": "Long-Life Oil Filter",
        "manufacturer": "MANN-FILTER",
        "category": "Filters",
        "price": "12.40",
        "description": ("Long-life oil filter for extended service applications."),
    },
    {
        "sku": "MANN-AF-001",
        "name": "High-Flow Air Filter",
        "manufacturer": "MANN-FILTER",
        "category": "Filters",
        "price": "21.80",
        "description": ("High-flow engine air filter for efficient intake filtration."),
    },
    {
        "sku": "MANN-CF-001",
        "name": "Cabin Air Filter",
        "manufacturer": "MANN-FILTER",
        "category": "Filters",
        "price": "16.70",
        "description": ("Cabin filter designed to reduce dust and airborne particles."),
    },
    {
        "sku": "MAH-TH-001",
        "name": "Engine Thermostat",
        "manufacturer": "MAHLE",
        "category": "Cooling System",
        "price": "34.90",
        "description": ("Engine coolant thermostat for temperature regulation."),
    },
    {
        "sku": "MAH-PR-001",
        "name": "Piston Ring Set",
        "manufacturer": "MAHLE",
        "category": "Engine Parts",
        "price": "84.00",
        "description": (
            "Replacement piston ring set for engine overhaul applications."
        ),
    },
    {
        "sku": "MAH-OF-001",
        "name": "Oil Filter",
        "manufacturer": "MAHLE",
        "category": "Filters",
        "price": "10.80",
        "description": ("Standard replacement engine oil filter."),
    },
    {
        "sku": "SKF-WB-001",
        "name": "Front Wheel Bearing Kit",
        "manufacturer": "SKF",
        "category": "Suspension",
        "price": "88.50",
        "description": ("Front wheel bearing service kit."),
    },
    {
        "sku": "SKF-WB-002",
        "name": "Rear Wheel Bearing Kit",
        "manufacturer": "SKF",
        "category": "Suspension",
        "price": "79.90",
        "description": ("Rear wheel bearing service kit."),
    },
    {
        "sku": "SKF-TK-001",
        "name": "Timing Tensioner Kit",
        "manufacturer": "SKF",
        "category": "Belts & Timing",
        "price": "115.00",
        "description": ("Timing drive tensioner kit for scheduled maintenance."),
    },
    {
        "sku": "SAC-SH-001",
        "name": "Front Shock Absorber",
        "manufacturer": "SACHS",
        "category": "Suspension",
        "price": "129.00",
        "description": ("Front axle gas pressure shock absorber."),
    },
    {
        "sku": "SAC-SH-002",
        "name": "Rear Shock Absorber",
        "manufacturer": "SACHS",
        "category": "Suspension",
        "price": "109.00",
        "description": ("Rear axle gas pressure shock absorber."),
    },
    {
        "sku": "SAC-CL-001",
        "name": "Clutch Release Bearing",
        "manufacturer": "SACHS",
        "category": "Engine Parts",
        "price": "58.00",
        "description": ("Clutch release bearing for manual transmission applications."),
    },
    {
        "sku": "NGK-SP-001",
        "name": "Iridium Spark Plug",
        "manufacturer": "NGK",
        "category": "Ignition",
        "price": "14.90",
        "description": ("Iridium spark plug for modern petrol engines."),
    },
    {
        "sku": "NGK-SP-002",
        "name": "Standard Spark Plug",
        "manufacturer": "NGK",
        "category": "Ignition",
        "price": "7.50",
        "description": ("Standard nickel spark plug for routine replacement."),
    },
    {
        "sku": "NGK-IG-001",
        "name": "Ignition Coil",
        "manufacturer": "NGK",
        "category": "Ignition",
        "price": "62.00",
        "description": ("Electronic ignition coil for coil-on-plug systems."),
    },
    {
        "sku": "DEN-SP-001",
        "name": "Iridium Spark Plug",
        "manufacturer": "DENSO",
        "category": "Ignition",
        "price": "15.50",
        "description": ("Fine-electrode iridium spark plug for petrol engines."),
    },
    {
        "sku": "DEN-IG-001",
        "name": "Ignition Coil",
        "manufacturer": "DENSO",
        "category": "Ignition",
        "price": "64.00",
        "description": ("Replacement electronic ignition coil."),
    },
    {
        "sku": "DEN-CS-001",
        "name": "Crankshaft Position Sensor",
        "manufacturer": "DENSO",
        "category": "Electrical",
        "price": "49.90",
        "description": ("Crankshaft position sensor for engine speed monitoring."),
    },
    {
        "sku": "GAT-TB-001",
        "name": "Timing Belt",
        "manufacturer": "Gates",
        "category": "Belts & Timing",
        "price": "43.00",
        "description": ("Engine timing belt for scheduled timing drive replacement."),
    },
    {
        "sku": "GAT-AB-001",
        "name": "Auxiliary Drive Belt",
        "manufacturer": "Gates",
        "category": "Belts & Timing",
        "price": "26.50",
        "description": ("Multi-rib auxiliary drive belt."),
    },
    {
        "sku": "CON-TK-001",
        "name": "Timing Belt Kit",
        "manufacturer": "Continental",
        "category": "Belts & Timing",
        "price": "119.00",
        "description": ("Complete timing belt service kit."),
    },
    {
        "sku": "CON-WP-001",
        "name": "Water Pump",
        "manufacturer": "Continental",
        "category": "Cooling System",
        "price": "78.00",
        "description": ("Mechanical engine coolant water pump."),
    },
]


SUPPLIERS = [
    {
        "name": "AutoParts Distribution Europe",
        "contact_person": "Martin Keller",
        "email": "sales@autoparts-europe.example",
        "phone": "+49 000 100 100",
        "address": "Hamburg, Germany",
        "tax_id": "DEMO-SUP-001",
    },
    {
        "name": "Central Europe Parts Hub",
        "contact_person": "Anna Novak",
        "email": "orders@ce-parts.example",
        "phone": "+48 000 200 200",
        "address": "Warsaw, Poland",
        "tax_id": "DEMO-SUP-002",
    },
    {
        "name": "Balkan Automotive Supply",
        "contact_person": "Marko Petrov",
        "email": "trade@balkan-auto.example",
        "phone": "+359 000 300 300",
        "address": "Sofia, Bulgaria",
        "tax_id": "DEMO-SUP-003",
    },
    {
        "name": "Nordic Components Trade",
        "contact_person": "Erik Lund",
        "email": "sales@nordic-components.example",
        "phone": "+46 000 400 400",
        "address": "Gothenburg, Sweden",
        "tax_id": "DEMO-SUP-004",
    },
    {
        "name": "Ukrainian Auto Distribution",
        "contact_person": "Oleksandr Kovalenko",
        "email": "orders@ua-distribution.example",
        "phone": "+380 00 000 5000",
        "address": "Kyiv, Ukraine",
        "tax_id": "DEMO-SUP-005",
    },
    {
        "name": "Global Brake & Filter Supply",
        "contact_person": "Laura Conti",
        "email": "wholesale@global-bf.example",
        "phone": "+39 000 600 600",
        "address": "Milan, Italy",
        "tax_id": "DEMO-SUP-006",
    },
]


CUSTOMERS = [
    {
        "name": "AutoService Premium",
        "contact_person": "Andrii Melnyk",
        "email": "service@premium-auto.example",
        "phone": "+380 00 001 0001",
        "address": "Odesa, Ukraine",
        "tax_id": "DEMO-CUS-001",
    },
    {
        "name": "DriveLine Service Center",
        "contact_person": "Dmytro Bondar",
        "email": "parts@driveline.example",
        "phone": "+380 00 001 0002",
        "address": "Odesa, Ukraine",
        "tax_id": "DEMO-CUS-002",
    },
    {
        "name": "MotorHub Odesa",
        "contact_person": "Serhii Tkachenko",
        "email": "orders@motorhub.example",
        "phone": "+380 00 001 0003",
        "address": "Odesa, Ukraine",
        "tax_id": "DEMO-CUS-003",
    },
    {
        "name": "West Auto Garage",
        "contact_person": "Roman Hrytsenko",
        "email": "garage@westauto.example",
        "phone": "+380 00 001 0004",
        "address": "Lviv, Ukraine",
        "tax_id": "DEMO-CUS-004",
    },
    {
        "name": "FleetPro Logistics",
        "contact_person": "Iryna Koval",
        "email": "fleet@fleetpro.example",
        "phone": "+380 00 001 0005",
        "address": "Kyiv, Ukraine",
        "tax_id": "DEMO-CUS-005",
    },
    {
        "name": "City Taxi Service",
        "contact_person": "Maksym Savchuk",
        "email": "maintenance@citytaxi.example",
        "phone": "+380 00 001 0006",
        "address": "Kyiv, Ukraine",
        "tax_id": "DEMO-CUS-006",
    },
    {
        "name": "AutoMaster Kyiv",
        "contact_person": "Olena Marchenko",
        "email": "parts@automaster.example",
        "phone": "+380 00 001 0007",
        "address": "Kyiv, Ukraine",
        "tax_id": "DEMO-CUS-007",
    },
    {
        "name": "RoadLine Service",
        "contact_person": "Bohdan Kravets",
        "email": "orders@roadline.example",
        "phone": "+380 00 001 0008",
        "address": "Lviv, Ukraine",
        "tax_id": "DEMO-CUS-008",
    },
]


WAREHOUSES = [
    {
        "code": "ODS-MAIN",
        "name": "Odesa Main Warehouse",
        "address": "Odesa, Ukraine",
    },
    {
        "code": "KYV-01",
        "name": "Kyiv Distribution Center",
        "address": "Kyiv, Ukraine",
    },
    {
        "code": "LVI-01",
        "name": "Lviv Regional Warehouse",
        "address": "Lviv, Ukraine",
    },
]


REORDER_LEVELS = {
    "Brake System": 10,
    "Filters": 12,
    "Ignition": 8,
    "Engine Parts": 6,
    "Suspension": 4,
    "Belts & Timing": 5,
    "Electrical": 6,
    "Cooling System": 5,
}


class Command(BaseCommand):
    help = "Reset business data and populate the database with a complete demo dataset."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help=(
                "Delete existing business/demo data before seeding. "
                "Users, groups and system configuration are preserved."
            ),
        )

    def handle(self, *args, **options):
        if not options["reset"]:
            raise CommandError(
                "This command requires --reset because it deletes "
                "existing business data."
            )

        self.stdout.write(
            self.style.WARNING(
                "Resetting business data. Users and roles will be preserved."
            )
        )

        with transaction.atomic():
            users = self._get_demo_users()

            self._clear_business_data()

            self._enable_demo_notifications()

            categories = self._create_categories()
            manufacturers = self._create_manufacturers()

            products = self._create_products(
                categories=categories,
                manufacturers=manufacturers,
            )

            suppliers = self._create_suppliers()
            customers = self._create_customers()
            warehouses = self._create_warehouses()

            purchase_orders = self._create_purchase_orders(
                users=users,
                suppliers=suppliers,
                warehouses=warehouses,
                products=products,
            )

            self._configure_reorder_levels()

            sales_orders = self._create_sales_orders(
                users=users,
                customers=customers,
                warehouses=warehouses,
                products=products,
            )

            self._create_manual_adjustments(
                users=users,
                warehouses=warehouses,
                products=products,
            )

        self._print_summary(
            purchase_orders=purchase_orders,
            sales_orders=sales_orders,
        )

    def _get_demo_users(self):
        def role_user(role_name):
            return (
                User.objects.filter(
                    is_active=True,
                    groups__name=role_name,
                )
                .order_by("id")
                .first()
            )

        sales_manager = role_user("Sales Manager")

        purchasing_manager = role_user("Purchasing Manager")

        warehouse_employee = role_user("Warehouse Employee")

        administrator = role_user("Administrator")

        if administrator is None:
            administrator = (
                User.objects.filter(
                    is_active=True,
                    is_superuser=True,
                )
                .order_by("id")
                .first()
            )

        missing = []

        if sales_manager is None:
            missing.append("Sales Manager")

        if purchasing_manager is None:
            missing.append("Purchasing Manager")

        if warehouse_employee is None:
            missing.append("Warehouse Employee")

        if administrator is None:
            missing.append("Administrator / superuser")

        if missing:
            raise CommandError(
                "Active users are required for these roles: " + ", ".join(missing)
            )

        return {
            "administrator": administrator,
            "sales_manager": sales_manager,
            "purchasing_manager": purchasing_manager,
            "warehouse_employee": warehouse_employee,
        }

    def _clear_business_data(self):
        Notification.objects.all().delete()

        StockReservation.objects.all().delete()
        StockMovement.objects.all().delete()

        SalesOrder.objects.all().delete()
        PurchaseOrder.objects.all().delete()

        Stock.objects.all().delete()
        Warehouse.objects.all().delete()

        Product.objects.all().delete()
        Category.objects.all().delete()
        Manufacturer.objects.all().delete()

        Customer.objects.all().delete()
        Supplier.objects.all().delete()

    def _enable_demo_notifications(self):
        settings = SystemSettings.load()

        settings.order_notifications_enabled = True
        settings.low_stock_notifications_enabled = True

        settings.save(
            update_fields=(
                "order_notifications_enabled",
                "low_stock_notifications_enabled",
                "updated_at",
            )
        )

    def _create_categories(self):
        result = {}

        for data in CATEGORIES:
            category = Category.objects.create(
                name=data["name"],
                slug=data["slug"],
                description=data["description"],
            )

            result[category.name] = category

        return result

    def _create_manufacturers(self):
        result = {}

        for data in MANUFACTURERS:
            manufacturer = Manufacturer.objects.create(
                name=data["name"],
                country=data["country"],
                website=data["website"],
            )

            result[manufacturer.name] = manufacturer

        return result

    def _create_products(
        self,
        *,
        categories,
        manufacturers,
    ):
        result = {}

        for data in PRODUCTS:
            product = Product.objects.create(
                sku=data["sku"],
                name=data["name"],
                description=data["description"],
                category=categories[data["category"]],
                manufacturer=manufacturers[data["manufacturer"]],
                sale_price=Decimal(data["price"]),
                is_active=True,
            )

            result[product.sku] = product

        return result

    def _create_suppliers(self):
        result = []

        for data in SUPPLIERS:
            result.append(
                Supplier.objects.create(
                    **data,
                    is_active=True,
                )
            )

        return result

    def _create_customers(self):
        result = []

        for data in CUSTOMERS:
            result.append(
                Customer.objects.create(
                    **data,
                    is_active=True,
                )
            )

        return result

    def _create_warehouses(self):
        result = {}

        for data in WAREHOUSES:
            warehouse = Warehouse.objects.create(
                **data,
                is_active=True,
            )

            result[warehouse.code] = warehouse

        return result

    def _purchase_price(self, product):
        return (product.sale_price * Decimal("0.68")).quantize(Decimal("0.01"))

    def _purchase_items(
        self,
        specs,
        products,
    ):
        return [
            {
                "product": products[sku],
                "quantity": quantity,
                "unit_price": self._purchase_price(products[sku]),
            }
            for sku, quantity in specs
        ]

    def _sales_items(
        self,
        specs,
        products,
    ):
        return [
            {
                "product": products[sku],
                "quantity": quantity,
                "unit_price": products[sku].sale_price,
            }
            for sku, quantity in specs
        ]

    def _create_purchase_orders(
        self,
        *,
        users,
        suppliers,
        warehouses,
        products,
    ):
        purchasing_manager = users["purchasing_manager"]

        warehouse_employee = users["warehouse_employee"]

        orders = []

        orders.append(
            self._purchase_order(
                supplier=suppliers[0],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 18),
                    ("BRM-BP-002", 24),
                    ("BRM-BD-001", 14),
                    ("BRM-BD-002", 12),
                    ("BOS-OF-001", 45),
                    ("BOS-AF-001", 30),
                    ("BOS-FU-001", 26),
                    ("BOS-OS-001", 16),
                    ("MANN-OF-001", 16),
                    ("MANN-AF-001", 28),
                    ("MANN-CF-001", 25),
                    ("MAH-TH-001", 18),
                    ("MAH-PR-001", 10),
                    ("MAH-OF-001", 32),
                    ("SKF-WB-001", 20),
                ],
                target_status="RECEIVED",
                created_days_ago=24,
                confirmed_days_ago=23,
                final_days_ago=21,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[1],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("SKF-WB-002", 18),
                    ("SKF-TK-001", 10),
                    ("SAC-SH-001", 14),
                    ("SAC-SH-002", 15),
                    ("SAC-CL-001", 12),
                    ("NGK-SP-001", 20),
                    ("NGK-SP-002", 40),
                    ("NGK-IG-001", 15),
                    ("DEN-SP-001", 22),
                    ("DEN-IG-001", 14),
                    ("DEN-CS-001", 16),
                    ("GAT-TB-001", 8),
                    ("GAT-AB-001", 20),
                    ("CON-TK-001", 9),
                    ("CON-WP-001", 13),
                ],
                target_status="RECEIVED",
                created_days_ago=20,
                confirmed_days_ago=19,
                final_days_ago=18,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[4],
                warehouse=warehouses["KYV-01"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 20),
                    ("BRM-BP-002", 18),
                    ("BRM-BD-001", 16),
                    ("BRM-BD-002", 14),
                    ("BOS-OF-001", 32),
                    ("BOS-AF-001", 28),
                    ("BOS-FU-001", 22),
                    ("BOS-OS-001", 14),
                    ("MANN-OF-001", 30),
                    ("MANN-AF-001", 24),
                    ("MANN-CF-001", 26),
                    ("MAH-TH-001", 15),
                ],
                target_status="RECEIVED",
                created_days_ago=16,
                confirmed_days_ago=15,
                final_days_ago=14,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[2],
                warehouse=warehouses["LVI-01"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("MANN-AF-001", 18),
                    ("MANN-CF-001", 20),
                    ("MAH-TH-001", 12),
                    ("MAH-PR-001", 8),
                    ("MAH-OF-001", 24),
                    ("SKF-WB-001", 12),
                    ("SKF-WB-002", 12),
                    ("SKF-TK-001", 8),
                    ("SAC-SH-001", 10),
                    ("SAC-SH-002", 10),
                    ("SAC-CL-001", 9),
                ],
                target_status="RECEIVED",
                created_days_ago=13,
                confirmed_days_ago=12,
                final_days_ago=11,
            )
        )

        # Confirmed replenishment for items that will
        # intentionally appear as low stock.
        orders.append(
            self._purchase_order(
                supplier=suppliers[5],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 30),
                    ("MANN-OF-001", 40),
                    ("NGK-SP-001", 36),
                    ("GAT-TB-001", 20),
                ],
                target_status="CONFIRMED",
                created_days_ago=3,
                confirmed_days_ago=2,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[3],
                warehouse=warehouses["KYV-01"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BD-001", 12),
                    ("SKF-WB-001", 10),
                    ("SAC-SH-001", 10),
                    ("CON-TK-001", 12),
                ],
                target_status="CONFIRMED",
                created_days_ago=2,
                confirmed_days_ago=1,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[4],
                warehouse=warehouses["LVI-01"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BOS-OF-001", 20),
                    ("MANN-CF-001", 20),
                    ("MAH-TH-001", 15),
                ],
                target_status="DRAFT",
                created_days_ago=1,
            )
        )

        orders.append(
            self._purchase_order(
                supplier=suppliers[0],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=purchasing_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BOS-AF-001", 18),
                    ("BOS-FU-001", 16),
                    ("GAT-AB-001", 14),
                ],
                target_status="CANCELLED",
                created_days_ago=8,
                confirmed_days_ago=7,
                final_days_ago=6,
            )
        )

        return orders

    def _purchase_order(
        self,
        *,
        supplier,
        warehouse,
        products,
        created_by,
        performed_by,
        items,
        target_status,
        created_days_ago,
        confirmed_days_ago=None,
        final_days_ago=None,
    ):
        order = create_purchase_order(
            created_by=created_by,
            supplier=supplier,
            warehouse=warehouse,
            items=self._purchase_items(
                items,
                products,
            ),
        )

        if target_status in {
            "CONFIRMED",
            "RECEIVED",
            "CANCELLED",
        }:
            confirm_purchase_order(order_id=order.pk)

        if target_status == "RECEIVED":
            receive_purchase_order(
                order_id=order.pk,
                performed_by=performed_by,
            )

        elif target_status == "CANCELLED":
            cancel_purchase_order(order_id=order.pk)

        self._backdate_purchase_order(
            order=order,
            created_days_ago=created_days_ago,
            confirmed_days_ago=confirmed_days_ago,
            final_days_ago=final_days_ago,
            target_status=target_status,
        )

        return order

    def _configure_reorder_levels(self):
        stocks = list(
            Stock.objects.select_related(
                "product",
                "product__category",
            )
        )

        for stock in stocks:
            stock.reorder_level = REORDER_LEVELS.get(
                stock.product.category.name,
                5,
            )

        Stock.objects.bulk_update(
            stocks,
            ["reorder_level"],
        )

    def _create_sales_orders(
        self,
        *,
        users,
        customers,
        warehouses,
        products,
    ):
        sales_manager = users["sales_manager"]

        warehouse_employee = users["warehouse_employee"]

        orders = []

        orders.append(
            self._sales_order(
                customer=customers[0],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 5),
                    ("MANN-OF-001", 3),
                    ("NGK-SP-001", 6),
                ],
                target_status="SHIPPED",
                created_days_ago=10,
                confirmed_days_ago=9,
                final_days_ago=8,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[1],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("NGK-SP-001", 7),
                    ("GAT-TB-001", 4),
                    ("BOS-OF-001", 10),
                ],
                target_status="SHIPPED",
                created_days_ago=7,
                confirmed_days_ago=6,
                final_days_ago=5,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[2],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 3),
                    ("MANN-OF-001", 4),
                    ("BRM-BD-001", 2),
                ],
                target_status="SHIPPED",
                created_days_ago=4,
                confirmed_days_ago=3,
                final_days_ago=2,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[4],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-001", 3),
                    ("MANN-OF-001", 2),
                ],
                target_status="CONFIRMED",
                created_days_ago=2,
                confirmed_days_ago=1,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[5],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("DEN-SP-001", 4),
                    ("DEN-IG-001", 2),
                ],
                target_status="CONFIRMED",
                created_days_ago=1,
                confirmed_days_ago=0.5,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[6],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BOS-OS-001", 2),
                    ("DEN-CS-001", 2),
                ],
                target_status="PROCESSING",
                created_days_ago=3,
                confirmed_days_ago=2,
                final_days_ago=1,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[7],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("SKF-WB-001", 3),
                    ("SKF-WB-002", 2),
                ],
                target_status="PROCESSING",
                created_days_ago=2,
                confirmed_days_ago=1.5,
                final_days_ago=0.75,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[3],
                warehouse=warehouses["ODS-MAIN"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BP-002", 2),
                    ("MANN-AF-001", 2),
                ],
                target_status="CANCELLED",
                created_days_ago=6,
                confirmed_days_ago=5,
                final_days_ago=4,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[0],
                warehouse=warehouses["KYV-01"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("BRM-BD-001", 2),
                    ("BOS-AF-001", 3),
                ],
                target_status="DRAFT",
                created_days_ago=0.5,
            )
        )

        orders.append(
            self._sales_order(
                customer=customers[4],
                warehouse=warehouses["LVI-01"],
                products=products,
                created_by=sales_manager,
                performed_by=warehouse_employee,
                items=[
                    ("SAC-SH-001", 2),
                    ("SKF-TK-001", 1),
                ],
                target_status="DRAFT",
                created_days_ago=0.25,
            )
        )

        return orders

    def _sales_order(
        self,
        *,
        customer,
        warehouse,
        products,
        created_by,
        performed_by,
        items,
        target_status,
        created_days_ago,
        confirmed_days_ago=None,
        final_days_ago=None,
    ):
        order = create_sales_order(
            created_by=created_by,
            customer=customer,
            warehouse=warehouse,
            items=self._sales_items(
                items,
                products,
            ),
        )

        if target_status in {
            "CONFIRMED",
            "PROCESSING",
            "SHIPPED",
            "CANCELLED",
        }:
            confirm_sales_order(order_id=order.pk)

        if target_status in {
            "PROCESSING",
            "SHIPPED",
        }:
            start_processing_sales_order(order_id=order.pk)

        if target_status == "SHIPPED":
            ship_sales_order(
                order_id=order.pk,
                performed_by=performed_by,
            )

        elif target_status == "CANCELLED":
            cancel_sales_order(order_id=order.pk)

        self._backdate_sales_order(
            order=order,
            created_days_ago=created_days_ago,
            confirmed_days_ago=confirmed_days_ago,
            final_days_ago=final_days_ago,
            target_status=target_status,
        )

        return order

    def _create_manual_adjustments(
        self,
        *,
        users,
        warehouses,
        products,
    ):
        administrator = users["administrator"]

        adjustments = [
            (
                "ODS-MAIN",
                "MANN-CF-001",
                5,
                "Cycle count correction after shelf audit.",
                1.5,
            ),
            (
                "ODS-MAIN",
                "BOS-FU-001",
                -2,
                "Damaged packaging removed from sellable stock.",
                1.0,
            ),
            (
                "ODS-MAIN",
                "CON-WP-001",
                -1,
                "Quality inspection write-off.",
                0.5,
            ),
        ]

        for (
            warehouse_code,
            sku,
            quantity,
            reason,
            days_ago,
        ) in adjustments:
            stock = Stock.objects.get(
                warehouse=warehouses[warehouse_code],
                product=products[sku],
            )

            adjust_stock(
                stock_id=stock.pk,
                quantity=quantity,
                reason=reason,
                performed_by=administrator,
            )

            movement = (
                StockMovement.objects.filter(
                    stock=stock,
                    reason=reason,
                )
                .order_by("-id")
                .first()
            )

            if movement:
                StockMovement.objects.filter(pk=movement.pk).update(
                    created_at=self._ago(days_ago)
                )

    def _ago(self, days):
        return timezone.now() - timedelta(days=days)

    def _backdate_purchase_order(
        self,
        *,
        order,
        created_days_ago,
        confirmed_days_ago,
        final_days_ago,
        target_status,
    ):
        created_at = self._ago(created_days_ago)

        updates = {
            "created_at": created_at,
            "updated_at": created_at,
        }

        confirmed_at = None
        final_at = None

        if confirmed_days_ago is not None:
            confirmed_at = self._ago(confirmed_days_ago)

            updates["confirmed_at"] = confirmed_at

            updates["updated_at"] = confirmed_at

        if final_days_ago is not None:
            final_at = self._ago(final_days_ago)

            updates["updated_at"] = final_at

        if target_status == "RECEIVED" and final_at is not None:
            updates["received_at"] = final_at

            StockMovement.objects.filter(
                purchase_order_item__purchase_order=order
            ).update(created_at=final_at)

        if target_status == "CANCELLED" and final_at is not None:
            updates["cancelled_at"] = final_at

        PurchaseOrder.objects.filter(pk=order.pk).update(**updates)

    def _backdate_sales_order(
        self,
        *,
        order,
        created_days_ago,
        confirmed_days_ago,
        final_days_ago,
        target_status,
    ):
        created_at = self._ago(created_days_ago)

        updates = {
            "created_at": created_at,
            "updated_at": created_at,
        }

        confirmed_at = None
        final_at = None

        if confirmed_days_ago is not None:
            confirmed_at = self._ago(confirmed_days_ago)

            updates["confirmed_at"] = confirmed_at

            updates["updated_at"] = confirmed_at

            StockReservation.objects.filter(sales_order_item__sales_order=order).update(
                created_at=confirmed_at
            )

        if final_days_ago is not None:
            final_at = self._ago(final_days_ago)

            updates["updated_at"] = final_at

        if target_status == "SHIPPED" and final_at is not None:
            updates["shipped_at"] = final_at

            StockMovement.objects.filter(sales_order_item__sales_order=order).update(
                created_at=final_at
            )

        if target_status == "CANCELLED" and final_at is not None:
            updates["cancelled_at"] = final_at

            StockReservation.objects.filter(
                sales_order_item__sales_order=order,
                status=(StockReservation.Status.RELEASED),
            ).update(released_at=final_at)

        SalesOrder.objects.filter(pk=order.pk).update(**updates)

    def _print_summary(
        self,
        *,
        purchase_orders,
        sales_orders,
    ):
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Demo dataset created successfully."))

        self.stdout.write(f"Manufacturers: {Manufacturer.objects.count()}")

        self.stdout.write(f"Categories: {Category.objects.count()}")

        self.stdout.write(f"Products: {Product.objects.count()}")

        self.stdout.write(f"Suppliers: {Supplier.objects.count()}")

        self.stdout.write(f"Customers: {Customer.objects.count()}")

        self.stdout.write(f"Warehouses: {Warehouse.objects.count()}")

        self.stdout.write(f"Stock rows: {Stock.objects.count()}")

        self.stdout.write(f"Purchase Orders: {len(purchase_orders)}")

        self.stdout.write(f"Sales Orders: {len(sales_orders)}")

        self.stdout.write(f"Reservations: {StockReservation.objects.count()}")

        self.stdout.write(f"Stock Movements: {StockMovement.objects.count()}")

        self.stdout.write(f"Notifications: {Notification.objects.count()}")

        low_stock_count = Stock.objects.filter(
            quantity__lte=models.F("reorder_level")
        ).count()

        self.stdout.write(f"Physical low-stock rows: {low_stock_count}")

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("Users, groups and roles were not modified.")
        )
