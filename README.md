# Inventory & Order Management System

A full-stack inventory and order management application built with Django for managing products, warehouses, stock, suppliers, customers, sales orders, purchase orders, reservations, stock movements and role-based workflows.

The project is designed around a wholesale auto-parts business, but the domain model is generic enough to be adapted to other inventory-based businesses.

---

## Features

### Inventory Management

- Multiple warehouses
- Physical stock tracking
- Available stock calculation
- Reorder levels
- Low-stock detection
- Manual stock adjustments
- Immutable stock movement history
- Stock reservations for confirmed sales orders

Available stock is calculated as:

```text
available stock = physical stock - active reservations
```

Stock quantity is never changed directly by order views. Inventory changes are handled through transactional service functions.

---

### Product Catalog

Products are organized using:

- Categories
- Manufacturers
- SKU
- Product descriptions
- Sale prices
- Active / inactive status

The demo dataset contains 30 automotive products from manufacturers such as:

- Brembo
- Bosch
- MANN-FILTER
- MAHLE
- SKF
- SACHS
- NGK
- DENSO
- Gates
- Continental

---

### Sales Orders

Sales orders follow a controlled lifecycle:

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

When a sales order is confirmed:

- stock availability is checked;
- stock reservations are created;
- physical stock is not reduced yet.

When an order is shipped:

- physical stock is reduced;
- reservations become `CONSUMED`;
- `SALES_SHIPMENT` stock movements are created;
- low-stock conditions are checked.

When a confirmed order is cancelled:

- active reservations become `RELEASED`;
- physical stock remains unchanged.

---

### Purchase Orders

Purchase orders follow this lifecycle:

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

When a purchase order is received:

- stock rows are created when necessary;
- physical inventory is increased;
- `PURCHASE_RECEIPT` movements are recorded.

Historical purchase prices are stored directly on purchase order items.

---

## Stock Movements

All inventory changes are recorded as stock movements.

Supported movement types:

```text
PURCHASE_RECEIPT
SALES_SHIPMENT
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

Manual quantity changes are performed through the stock adjustment service and require a reason.

This provides a traceable history of inventory changes.

---

## Stock Reservations

Reservations connect sales orders with warehouse inventory.

Supported statuses:

```text
ACTIVE
RELEASED
CONSUMED
```

Example:

```text
Sales Order confirmed
        ↓
ACTIVE reservation
        ↓
Order processing
        ↓
Order shipped
        ↓
CONSUMED reservation
```

If the confirmed order is cancelled instead:

```text
ACTIVE
   ↓
RELEASED
```

---

## Role-Based Access Control

The application uses Django Groups and Permissions instead of storing a custom role field directly on the user.

Four application roles are provided.

### Administrator

Can manage:

- users and roles;
- products;
- categories;
- manufacturers;
- customers;
- suppliers;
- warehouses;
- system settings.

Administrators can also perform manual stock adjustments.

Administrators still follow the normal order lifecycle and cannot bypass business rules.

### Sales Manager

Can:

- manage customers;
- view the product catalog;
- view stock availability;
- create and edit draft sales orders;
- confirm sales orders;
- cancel eligible sales orders.

Cannot:

- adjust stock;
- receive purchase orders;
- manage suppliers;
- manage users.

### Purchasing Manager

Can:

- manage suppliers;
- view products and stock;
- create purchase orders;
- edit draft purchase orders;
- confirm purchase orders;
- cancel eligible purchase orders.

Cannot:

- manage sales orders;
- adjust stock;
- receive warehouse deliveries;
- manage users.

### Warehouse Employee

Can:

- view products;
- view stock;
- view reservations;
- view stock movements;
- process confirmed sales orders;
- ship sales orders;
- receive confirmed purchase orders.

Cannot:

- create commercial orders;
- edit customers or suppliers;
- change prices;
- perform manual stock adjustments;
- manage users.

---

## Dashboard

The dashboard provides an operational overview of the business.

It includes:

- active products;
- low-stock items;
- open sales orders;
- open sales order value;
- open purchase orders;
- open purchase order value;
- recent sales orders;
- recent purchase orders;
- low-stock overview.

Dashboard data respects the permissions of the currently authenticated user.

---

## Notifications

The application includes an internal notification system.

Notifications can be generated for:

- confirmed sales orders;
- shipped sales orders;
- confirmed purchase orders;
- received purchase orders;
- low-stock warnings.

Users can:

- view unread notifications;
- mark individual notifications as read;
- mark all notifications as read;
- open the related business object directly from a notification.

Notification redirects are validated to prevent unsafe external redirects.

---

## Global Search

The application includes a global search interface powered by HTMX.

Depending on user permissions, search results may include:

- products;
- customers;
- suppliers;
- sales orders;
- purchase orders.

---

## System Settings

Administrators can configure application-level settings directly from the web interface.

Supported settings include:

- company name;
- company description;
- sales order prefix;
- purchase order prefix;
- default reorder level;
- low-stock notifications;
- order notifications;
- items per page.

Company branding is automatically used in both the application sidebar and login page.

---

## REST API

The project also provides a REST API using Django REST Framework.

Main endpoints include:

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

The API supports filtering, searching, ordering and pagination where applicable.

---

## Authentication

The project uses two authentication approaches.

### Web Interface

The server-rendered web interface uses Django session authentication.

Login:

```text
/login/
```

### REST API

The API uses JWT authentication provided by Simple JWT.

Obtain access and refresh tokens:

```http
POST /api/auth/login/
```

Refresh an access token:

```http
POST /api/auth/refresh/
```

Example login body:

```json
{
  "email": "user@example.com",
  "password": "your-password"
}
```

Authenticated API requests use:

```http
Authorization: Bearer <access_token>
```

---

## API Documentation

Interactive Swagger documentation is available at:

```text
http://localhost:8000/api/docs/
```

OpenAPI schema:

```text
http://localhost:8000/api/schema/
```

The generated schema is also stored in:

```text
schema.yml
```

---

## Business Logic Architecture

HTTP views are intentionally kept separate from core business logic.

The project uses service functions for operations such as:

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

Critical inventory operations use:

- database transactions;
- `transaction.atomic`;
- `select_for_update`;
- model constraints.

This prevents order views from directly manipulating stock quantities and keeps inventory behavior consistent across the web interface and REST API.

---

## Technology Stack

### Backend

- Python 3.14
- Django 5.2
- Django REST Framework
- Simple JWT
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
- PostgreSQL
- GitHub Actions

---

## Project Structure

```text
django-inventory-order-management/
│
├── accounts/
│   ├── management/
│   ├── tests/
│   ├── forms.py
│   ├── models.py
│   ├── permissions.py
│   ├── services.py
│   └── web_views.py
│
├── catalog/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── web_views.py
│
├── partners/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── web_views.py
│
├── inventory/
│   ├── models.py
│   ├── services.py
│   ├── serializers.py
│   ├── views.py
│   └── web_views.py
│
├── sales/
│   ├── models.py
│   ├── services.py
│   ├── serializers.py
│   ├── views.py
│   └── web_views.py
│
├── purchasing/
│   ├── models.py
│   ├── services.py
│   ├── serializers.py
│   ├── views.py
│   └── web_views.py
│
├── notifications/
│
├── core/
│   └── management/
│       └── commands/
│           └── seed_demo_data.py
│
├── templates/
├── static/
├── config/
│
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── schema.yml
└── manage.py
```

---

## Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/Eugene-Plitka/django-inventory-order-management.git
cd django-inventory-order-management
```

### 2. Create the environment file

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

Do not use development secrets in production.

### 3. Build and start the containers

```bash
docker compose up -d --build
```

### 4. Run migrations

```bash
docker compose exec web python manage.py migrate
```

### 5. Create application roles

```bash
docker compose exec web python manage.py setup_roles
```

This creates and configures:

```text
Administrator
Sales Manager
Purchasing Manager
Warehouse Employee
```

### 6. Create a superuser

```bash
docker compose exec web python manage.py createsuperuser
```

The custom user model uses email for authentication.

### 7. Open the application

Application:

```text
http://localhost:8000/
```

Login page:

```text
http://localhost:8000/login/
```

Django Admin:

```text
http://localhost:8000/admin/
```

Swagger API documentation:

```text
http://localhost:8000/api/docs/
```

---

## Demo Dataset

The repository contains a custom Django management command for generating a complete demonstration dataset.

Before running it, create active users for these roles:

```text
Administrator
Sales Manager
Purchasing Manager
Warehouse Employee
```

Users can be created from the application's **Users & Roles** section or through Django Admin.

Then run:

```bash
docker compose exec web python manage.py seed_demo_data --reset
```

> **Warning**
>
> `--reset` deletes existing business data before creating the demo dataset.
> Users, groups, roles and system settings are preserved.

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
stock reservations
stock movements
notifications
low-stock scenarios
```

It intentionally creates multiple lifecycle states.

Sales orders include:

```text
DRAFT
CONFIRMED
PROCESSING
SHIPPED
CANCELLED
```

Purchase orders include:

```text
DRAFT
CONFIRMED
RECEIVED
CANCELLED
```

Reservations include:

```text
ACTIVE
RELEASED
CONSUMED
```

Stock movements include:

```text
PURCHASE_RECEIPT
SALES_SHIPMENT
ADJUSTMENT_IN
ADJUSTMENT_OUT
```

This makes it possible to explore most of the system functionality immediately after setup.

---

## Running Tests

Run the complete test suite:

```bash
docker compose exec web python manage.py test
```

Check the Django project:

```bash
docker compose exec web python manage.py check
```

Check for missing migrations:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

---

## Continuous Integration

GitHub Actions runs the following checks on pushes and pull requests:

```text
Django system check
Migration check
Database migrations
Automated test suite
```

The CI environment uses PostgreSQL.

---

## Data Integrity

Several safeguards are implemented at both service and database levels.

Examples include:

- unique product SKU;
- unique stock row per product and warehouse;
- unique product per sales order;
- unique product per purchase order;
- positive order quantities;
- non-negative product prices;
- non-zero stock movements;
- stock cannot become negative through manual adjustment;
- order lifecycle transitions are validated;
- inventory updates are transaction-safe.

---

## Security Considerations

The project includes:

- Django password validation;
- CSRF protection for the web interface;
- session authentication;
- JWT authentication for the REST API;
- role-based permissions;
- POST-only state-changing order actions;
- ownership checks for notifications;
- validated redirect targets;
- protection against an administrator deactivating their own account;
- protection against an administrator removing their own Administrator role;
- protection against non-superuser administrators editing Django superusers.

Production deployment should additionally configure:

```text
DEBUG=False
ALLOWED_HOSTS
SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
SECURE_HSTS_SECONDS
```

Production JWT lifetime and refresh-token policies should also be reviewed before deployment.

---

## Current Status

The project currently includes:

- complete product catalog management;
- customers and suppliers;
- multi-warehouse inventory;
- sales order lifecycle;
- purchase order lifecycle;
- stock reservations;
- stock movement history;
- manual stock adjustments;
- low-stock monitoring;
- internal notifications;
- dashboard analytics;
- global search;
- role-based UI;
- users and roles management;
- configurable system settings;
- REST API;
- Swagger / OpenAPI documentation;
- demo data generation;
- automated tests;
- GitHub Actions CI.

---

## License

This project was created as a portfolio and learning project.

Third-party product and manufacturer names used in the demonstration dataset belong to their respective owners. Demo SKUs, supplier records, customer records and transaction data are fictional and are included only for demonstration purposes.
