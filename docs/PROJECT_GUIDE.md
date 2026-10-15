# Inventory & Order Management System — Project Guide

This document contains the detailed documentation for the Inventory & Order Management System portfolio project.

The application is designed around a wholesale auto-parts business, but the architecture and business model can be adapted to other inventory-based systems.

---

## 1. Project Overview

The project combines a Django server-rendered web interface, a REST API, role-based permissions, multi-warehouse inventory, sales and purchasing workflows, stock reservations, stock movement history, internal notifications, configurable system settings, demo dataset generation, automated tests and CI.

The core design goal is to keep inventory changes consistent and auditable. Order views do not directly modify stock quantities. Critical operations are handled by service functions using database transactions and row locking.

---

## 2. Technology Stack

### Backend

- Python 3.14
- Django 5.2
- Django REST Framework
- djangorestframework-simplejwt
- django-filter
- drf-spectacular
- PostgreSQL 18

### Frontend

- Django Templates
- HTMX
- Alpine.js
- HTML
- CSS
- JavaScript

### Infrastructure

- Docker
- Docker Compose
- GitHub Actions

---

## 3. Main Applications

### `accounts`

Custom email-based user model, authentication, profile management, roles and permissions, users and roles management, and global search support.

### `catalog`

Categories, manufacturers and products.

### `partners`

Customers and suppliers.

### `inventory`

Warehouses, stock, reservations, stock movements and manual stock adjustments.

### `sales`

Sales orders, sales order items and sales lifecycle operations.

### `purchasing`

Purchase orders, purchase order items and purchasing lifecycle operations.

### `notifications`

Internal notifications, unread counts, mark-as-read actions and related-object links.

### `core`

System settings, shared pagination logic, template helpers and demo dataset generation.

---

## 4. Product Catalog

A product contains:

- SKU;
- name;
- description;
- category;
- manufacturer;
- current sale price;
- active/inactive status.

The current base sale price is stored in `Product.sale_price`.

Historical prices are stored in:

- `SalesOrderItem.unit_price`
- `PurchaseOrderItem.unit_price`

This keeps historical orders unchanged when product prices are updated later.

---

## 5. Warehouses and Stock

The project supports multiple warehouses.

A stock row connects:

```text
Product + Warehouse
```

and stores physical quantity and reorder level.

Only one stock row can exist for the same product and warehouse.

Available stock is calculated as:

```text
available = physical quantity - ACTIVE reservations
```

Confirming a sales order reserves inventory without immediately reducing physical stock.

---

## 6. Stock Reservations

Reservation statuses:

```text
ACTIVE
RELEASED
CONSUMED
```

Confirmed sales order:

```text
Sales Order
    ↓
CONFIRMED
    ↓
ACTIVE StockReservation
```

Cancelled confirmed order:

```text
ACTIVE
   ↓
RELEASED
```

Shipped order:

```text
ACTIVE
   ↓
CONSUMED
```

Physical stock is reduced only when the order is shipped.

---

## 7. Stock Movements

Every physical inventory change is recorded through `StockMovement`.

Supported movement types:

```text
PURCHASE_RECEIPT
SALES_SHIPMENT
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

Manual adjustments require a reason, creating an auditable inventory history.

---

## 8. Sales Order Workflow

Lifecycle:

```text
DRAFT
  │
  ├──> CONFIRMED
  │       │
  │       ├──> PROCESSING
  │       │       │
  │       │       └──> SHIPPED
  │       │
  │       └──> CANCELLED
  │
  └──> CANCELLED
```

### DRAFT

The Sales Manager can create and edit the order. No inventory is reserved.

### CONFIRMED

Stock availability is validated and active reservations are created. Physical stock is unchanged.

### PROCESSING

A Warehouse Employee starts warehouse processing. Reservations remain active.

### SHIPPED

Physical stock decreases, reservations become consumed, shipment movements are created and low-stock conditions are checked.

### CANCELLED

Draft orders can be cancelled directly. Confirmed orders can also be cancelled, which releases active reservations.

---

## 9. Purchase Order Workflow

Lifecycle:

```text
DRAFT
  │
  ├──> CONFIRMED
  │       │
  │       ├──> RECEIVED
  │       │
  │       └──> CANCELLED
  │
  └──> CANCELLED
```

### DRAFT

The Purchasing Manager can create and edit suppliers, warehouses, products, quantities and purchase prices.

### CONFIRMED

The order becomes expected inventory. Physical stock is unchanged.

### RECEIVED

Missing stock rows are created automatically, physical stock increases and purchase receipt movements are created.

### CANCELLED

Draft and confirmed purchase orders can be cancelled.

---

## 10. Roles and Permissions

The project uses Django Groups and Permissions.

Create or update roles with:

```bash
docker compose exec web python manage.py setup_roles
```

### Administrator

Can manage users, roles, catalog data, customers, suppliers, warehouses and system settings. Can also perform manual stock adjustments.

Administrators still follow order lifecycle rules.

Safeguards prevent a regular Administrator from deactivating their own account, removing their own Administrator role or editing a Django superuser.

### Sales Manager

Can manage customers, view catalog and stock, and create/edit/confirm/cancel eligible sales orders.

Cannot manually adjust stock, receive purchase orders, manage suppliers or manage users.

### Purchasing Manager

Can manage suppliers, view catalog and stock, and create/edit/confirm/cancel eligible purchase orders.

Cannot manage sales orders, receive warehouse deliveries, manually adjust stock or manage users.

### Warehouse Employee

Can view catalog, stock, reservations and movements, process/ship sales orders and receive purchase orders.

Cannot create commercial orders, manage partners, change prices, manually adjust stock or manage users.

---

## 11. Dashboard

The permission-aware dashboard can display:

- active products;
- low-stock count;
- open sales order count and value;
- open purchase order count and value;
- recent sales orders;
- recent purchase orders;
- low-stock items.

---

## 12. Global Search

HTMX-powered global search can return, depending on permissions:

- products;
- customers;
- suppliers;
- sales orders;
- purchase orders.

---

## 13. Notifications

Notification types include:

- sales order confirmed;
- sales order shipped;
- purchase order confirmed;
- purchase order received;
- low-stock warning.

Users can view unread notifications, mark individual or all notifications as read and navigate to related objects.

Submitted redirect targets are validated to prevent unsafe external redirects.

Notification generation can be enabled or disabled in System Settings.

---

## 14. System Settings

Administrators can configure:

- company name;
- company description;
- sales order prefix;
- purchase order prefix;
- default reorder level;
- low-stock notifications;
- order notifications;
- items per page.

Branding is shown in the sidebar and login page.

Order prefix changes apply only to newly created orders.

---

## 15. Authentication

### Web Interface

The web interface uses Django session authentication.

Login:

```text
http://localhost:8000/login/
```

The custom user model authenticates by email.

### REST API

The REST API uses JWT authentication through Simple JWT.

Obtain tokens:

```http
POST /api/auth/login/
```

Example:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Refresh:

```http
POST /api/auth/refresh/
```

Authenticated request:

```http
Authorization: Bearer <access_token>
```

---

## 16. REST API

Main resources:

```text
/api/products/
/api/categories/
/api/manufacturers/
/api/customers/
/api/suppliers/
/api/warehouses/
/api/stocks/
/api/stock-reservations/
/api/stock-movements/
/api/sales-orders/
/api/purchase-orders/
```

The API supports filtering, searching, ordering and pagination where configured.

---

## 17. API Documentation

Swagger UI:

```text
http://localhost:8000/api/docs/
```

OpenAPI schema endpoint:

```text
http://localhost:8000/api/schema/
```

Generated schema file:

```text
schema.yml
```

---

## 18. Business Logic Architecture

Critical business actions are implemented in service functions, including:

```text
confirm_sales_order()
cancel_sales_order()
start_processing_sales_order()
ship_sales_order()

confirm_purchase_order()
cancel_purchase_order()
receive_purchase_order()

adjust_stock()
```

Inventory-sensitive operations use:

- `transaction.atomic`;
- `select_for_update`;
- database constraints.

This keeps stock behavior consistent across the web interface and REST API.

---

## 19. Installation

### Requirements

- Docker
- Docker Compose
- Git

### Clone the Repository

```bash
git clone https://github.com/Eugene-Plitka/django-inventory-order-management.git
cd django-inventory-order-management
```

### Create `.env`

Copy `.env.example` to `.env`.

Example:

```env
DEBUG=True
SECRET_KEY=your-development-secret-key

POSTGRES_DB=inventory_db
POSTGRES_USER=inventory_user
POSTGRES_PASSWORD=your-database-password
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### Build and Start

```bash
docker compose up -d --build
```

### Run Migrations

```bash
docker compose exec web python manage.py migrate
```

### Create Roles

```bash
docker compose exec web python manage.py setup_roles
```

This creates or updates:

```text
Administrator
Sales Manager
Purchasing Manager
Warehouse Employee
```

### Create a Superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### Open the Application

Application:

```text
http://localhost:8000/
```

Login:

```text
http://localhost:8000/login/
```

Django Admin:

```text
http://localhost:8000/admin/
```

Swagger:

```text
http://localhost:8000/api/docs/
```

---

## 20. Creating Application Users

After logging in as an administrator, create application users from the **Users & Roles** section.

For the full demo dataset, create at least one active user for each role:

```text
Administrator
Sales Manager
Purchasing Manager
Warehouse Employee
```

---

## 21. Demo Dataset

Run:

```bash
docker compose exec web python manage.py seed_demo_data --reset
```

`--reset` deletes existing business data before creating the demo environment.

It preserves:

- users;
- groups;
- roles;
- system settings.

The seed command creates approximately:

```text
10 manufacturers
8 categories
30 products
6 suppliers
8 customers
3 warehouses
8 purchase orders
10 sales orders
50+ stock rows
```

It also creates reservations, stock movements, notifications and low-stock scenarios.

Demo lifecycle coverage:

Sales Orders:

```text
DRAFT
CONFIRMED
PROCESSING
SHIPPED
CANCELLED
```

Purchase Orders:

```text
DRAFT
CONFIRMED
RECEIVED
CANCELLED
```

Reservations:

```text
ACTIVE
RELEASED
CONSUMED
```

Stock Movements:

```text
PURCHASE_RECEIPT
SALES_SHIPMENT
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

Manufacturer names are based on real automotive brands. Demo SKUs, suppliers, customers and transaction data are fictional and are included only for demonstration purposes.

---

## 22. Testing

Run all tests:

```bash
docker compose exec web python manage.py test
```

Django system check:

```bash
docker compose exec web python manage.py check
```

Missing migration check:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

---

## 23. Continuous Integration

GitHub Actions runs on pushes and pull requests.

The CI workflow performs:

```text
Django system check
Migration check
Database migrations
Automated test suite
```

PostgreSQL is used in CI.

---

## 24. Data Integrity and Security

Important safeguards include:

- unique product SKU;
- unique stock row per product and warehouse;
- unique product per sales order;
- unique product per purchase order;
- positive order quantities;
- non-negative prices;
- non-zero stock movements;
- transaction-safe inventory operations;
- lifecycle validation;
- POST-only state-changing order actions;
- CSRF protection;
- notification ownership checks;
- validated redirect destinations;
- role-based access control;
- administrator self-lockout protections.

---

## 25. Production Deployment Notes

The current repository is primarily configured for local development and portfolio demonstration.

Before production deployment configure:

```text
DEBUG=False
ALLOWED_HOSTS
production SECRET_KEY
HTTPS
SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
SECURE_HSTS_SECONDS
```

Production deployment should also include proper static file handling, a production web server, database backups, logging, secure environment variable management and a reviewed JWT access/refresh token policy.

Do not enable HSTS until HTTPS is correctly configured.

---

## 26. Useful Commands

Start:

```bash
docker compose up -d
```

Stop:

```bash
docker compose down
```

Rebuild:

```bash
docker compose up -d --build
```

Migrate:

```bash
docker compose exec web python manage.py migrate
```

Roles:

```bash
docker compose exec web python manage.py setup_roles
```

Superuser:

```bash
docker compose exec web python manage.py createsuperuser
```

Demo data:

```bash
docker compose exec web python manage.py seed_demo_data --reset
```

Tests:

```bash
docker compose exec web python manage.py test
```

Django check:

```bash
docker compose exec web python manage.py check
```

Migration check:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

Regenerate OpenAPI schema:

```bash
docker compose exec web python manage.py spectacular --file schema.yml
```

---

## 27. Project Status

The project includes product catalog management, customers and suppliers, multi-warehouse inventory, sales and purchase workflows, reservations, stock movements, manual adjustments, low-stock monitoring, notifications, dashboard, global search, user/role management, system settings, REST API, JWT authentication, Swagger/OpenAPI, demo data generation, automated tests and CI.

It is intended as a portfolio demonstration of Django application architecture, business logic design, transactional inventory handling, access control, REST API development and full-stack web development.
