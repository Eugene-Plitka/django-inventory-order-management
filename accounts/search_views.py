from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from catalog.models import Product
from partners.models import Customer, Supplier
from purchasing.models import PurchaseOrder
from sales.models import SalesOrder


@login_required
def global_search(request):
    query = request.GET.get(
        "q",
        "",
    ).strip()

    context = {
        "query": query,
        "products": [],
        "customers": [],
        "suppliers": [],
        "sales_orders": [],
        "purchase_orders": [],
        "has_results": False,
    }

    if len(query) < 2:
        return render(
            request,
            "accounts/search/_results.html",
            context,
        )

    if request.user.has_perm("catalog.view_product"):
        context["products"] = (
            Product.objects.filter(Q(sku__icontains=query) | Q(name__icontains=query))
            .select_related(
                "category",
                "manufacturer",
            )
            .order_by("name")[:5]
        )

    if request.user.has_perm("partners.view_customer"):
        context["customers"] = Customer.objects.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(contact_person__icontains=query)
        ).order_by("name")[:5]

    if request.user.has_perm("partners.view_supplier"):
        context["suppliers"] = Supplier.objects.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(contact_person__icontains=query)
        ).order_by("name")[:5]

    if request.user.has_perm("sales.view_salesorder"):
        context["sales_orders"] = (
            SalesOrder.objects.filter(
                Q(order_number__icontains=query) | Q(customer__name__icontains=query)
            )
            .select_related(
                "customer",
                "warehouse",
            )
            .order_by("-created_at")[:5]
        )

    if request.user.has_perm("purchasing.view_purchaseorder"):
        context["purchase_orders"] = (
            PurchaseOrder.objects.filter(
                Q(order_number__icontains=query) | Q(supplier__name__icontains=query)
            )
            .select_related(
                "supplier",
                "warehouse",
            )
            .order_by("-created_at")[:5]
        )

    context["has_results"] = any(
        (
            context["products"],
            context["customers"],
            context["suppliers"],
            context["sales_orders"],
            context["purchase_orders"],
        )
    )

    return render(
        request,
        "accounts/search/_results.html",
        context,
    )
