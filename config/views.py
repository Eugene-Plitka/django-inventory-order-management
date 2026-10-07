from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import render

from catalog.models import Product
from inventory.models import (
    Stock,
    StockReservation,
)
from purchasing.models import PurchaseOrder
from sales.models import SalesOrder


@login_required
def dashboard(request):
    context = {
        "can_view_products": (request.user.has_perm("catalog.view_product")),
        "can_view_stock": (request.user.has_perm("inventory.view_stock")),
        "can_view_sales": (request.user.has_perm("sales.view_salesorder")),
        "can_view_purchases": (request.user.has_perm("purchasing.view_purchaseorder")),
    }

    if context["can_view_products"]:
        context["total_products"] = Product.objects.filter(is_active=True).count()

    if context["can_view_stock"]:
        stock_queryset = (
            Stock.objects.select_related(
                "product",
                "warehouse",
            )
            .annotate(
                reserved_quantity=Coalesce(
                    Sum(
                        "reservations__quantity",
                        filter=Q(reservations__status=(StockReservation.Status.ACTIVE)),
                    ),
                    Value(0),
                )
            )
            .annotate(available_quantity=(F("quantity") - F("reserved_quantity")))
        )

        low_stock_queryset = stock_queryset.filter(
            available_quantity__lte=F("reorder_level")
        )

        context["low_stock_count"] = low_stock_queryset.count()

        context["low_stock_items"] = low_stock_queryset.order_by(
            "available_quantity",
            "product__name",
        )[:6]

    if context["can_view_sales"]:
        open_sales_statuses = (
            SalesOrder.Status.DRAFT,
            SalesOrder.Status.CONFIRMED,
            SalesOrder.Status.PROCESSING,
        )

        sales_line_total = ExpressionWrapper(
            F("items__quantity") * F("items__unit_price"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )

        open_sales_queryset = SalesOrder.objects.filter(status__in=open_sales_statuses)

        context["open_sales_orders"] = open_sales_queryset.count()

        context["open_sales_value"] = open_sales_queryset.aggregate(
            total=Sum(sales_line_total)
        )["total"] or Decimal("0.00")

        context["recent_sales_orders"] = SalesOrder.objects.select_related(
            "customer",
            "warehouse",
        ).order_by("-created_at")[:6]

    if context["can_view_purchases"]:
        open_purchase_statuses = (
            PurchaseOrder.Status.DRAFT,
            PurchaseOrder.Status.CONFIRMED,
        )

        purchase_line_total = ExpressionWrapper(
            F("items__quantity") * F("items__unit_price"),
            output_field=DecimalField(
                max_digits=14,
                decimal_places=2,
            ),
        )

        open_purchase_queryset = PurchaseOrder.objects.filter(
            status__in=open_purchase_statuses
        )

        context["open_purchase_orders"] = open_purchase_queryset.count()

        context["open_purchase_value"] = open_purchase_queryset.aggregate(
            total=Sum(purchase_line_total)
        )["total"] or Decimal("0.00")

        context["recent_purchase_orders"] = PurchaseOrder.objects.select_related(
            "supplier",
            "warehouse",
        ).order_by("-created_at")[:6]

    return render(
        request,
        "dashboard/index.html",
        context,
    )
