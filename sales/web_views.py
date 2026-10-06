from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from inventory.models import StockReservation

from .exceptions import SalesOrderServiceError
from .forms import (
    SalesOrderForm,
    SalesOrderItemFormSet,
)
from .models import SalesOrder
from .services import (
    cancel_sales_order,
    confirm_sales_order,
    create_sales_order,
    ship_sales_order,
    start_processing_sales_order,
    update_sales_order,
)


def _has_role(user, *roles):
    if user.is_superuser:
        return True

    return user.groups.filter(name__in=roles).exists()


def _can_manage_sales_order(user):
    return _has_role(
        user,
        "Administrator",
        "Sales Manager",
    )


def _can_process_sales_order(user):
    return _has_role(
        user,
        "Administrator",
        "Warehouse Employee",
    )


def _build_items_from_formset(formset):
    items = []

    for form in formset:
        cleaned_data = getattr(
            form,
            "cleaned_data",
            None,
        )

        if not cleaned_data:
            continue

        if cleaned_data.get("DELETE"):
            continue

        product = cleaned_data.get("product")

        if product is None:
            continue

        items.append(
            {
                "product": product,
                "quantity": cleaned_data["quantity"],
                "unit_price": cleaned_data["unit_price"],
            }
        )

    return items


@login_required
@permission_required(
    "sales.view_salesorder",
    raise_exception=True,
)
def sales_order_list(request):
    orders = SalesOrder.objects.select_related(
        "customer",
        "warehouse",
        "created_by",
    ).prefetch_related(
        "items",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(customer__name__icontains=search)
            | Q(warehouse__code__icontains=search)
        )

    if status:
        orders = orders.filter(status=status)

    orders = orders.order_by("-created_at")

    paginator = Paginator(
        orders,
        20,
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "statuses": SalesOrder.Status.choices,
        "can_manage_sales": (_can_manage_sales_order(request.user)),
    }

    template_name = "sales/orders/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "sales/orders/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "sales.add_salesorder",
    raise_exception=True,
)
def sales_order_create(request):
    if not _can_manage_sales_order(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = SalesOrderForm(request.POST)

        item_formset = SalesOrderItemFormSet(
            request.POST,
            prefix="items",
        )

        if form.is_valid() and item_formset.is_valid():
            order = create_sales_order(
                created_by=request.user,
                customer=form.cleaned_data["customer"],
                warehouse=form.cleaned_data["warehouse"],
                items=(_build_items_from_formset(item_formset)),
            )

            messages.success(
                request,
                "Sales order created successfully.",
            )

            return redirect(
                "sales_web:sales-order-detail",
                pk=order.pk,
            )

    else:
        form = SalesOrderForm()

        item_formset = SalesOrderItemFormSet(
            prefix="items",
        )

    return render(
        request,
        "sales/orders/form.html",
        {
            "form": form,
            "item_formset": item_formset,
            "page_title": ("New Sales Order"),
            "page_subtitle": ("Create a draft customer sales order."),
            "submit_label": ("Create Order"),
        },
    )


@login_required
@permission_required(
    "sales.view_salesorder",
    raise_exception=True,
)
def sales_order_detail(request, pk):
    order = get_object_or_404(
        SalesOrder.objects.select_related(
            "customer",
            "warehouse",
            "created_by",
        ).prefetch_related(
            "items__product",
        ),
        pk=pk,
    )

    items = list(order.items.select_related("product").all())

    order_total = Decimal("0.00")

    for item in items:
        item.line_total = item.unit_price * item.quantity

        order_total += item.line_total

    reservations = (
        StockReservation.objects.select_related(
            "stock",
            "stock__product",
            "stock__warehouse",
            "sales_order_item",
        )
        .filter(sales_order_item__sales_order=order)
        .order_by("sales_order_item__product__name")
    )

    can_manage = _can_manage_sales_order(request.user)

    can_process = _can_process_sales_order(request.user)

    context = {
        "order": order,
        "items": items,
        "reservations": reservations,
        "order_total": order_total,
        "can_edit": (can_manage and order.status == SalesOrder.Status.DRAFT),
        "can_confirm": (can_manage and order.status == SalesOrder.Status.DRAFT),
        "can_cancel": (
            can_manage
            and order.status
            in {
                SalesOrder.Status.DRAFT,
                SalesOrder.Status.CONFIRMED,
            }
        ),
        "can_start_processing": (
            can_process and order.status == SalesOrder.Status.CONFIRMED
        ),
        "can_ship": (can_process and order.status == SalesOrder.Status.PROCESSING),
    }

    return render(
        request,
        "sales/orders/detail.html",
        context,
    )


@login_required
@permission_required(
    "sales.change_salesorder",
    raise_exception=True,
)
def sales_order_update(
    request,
    pk,
):
    if not _can_manage_sales_order(request.user):
        raise PermissionDenied

    order = get_object_or_404(
        SalesOrder.objects.select_related(
            "customer",
            "warehouse",
        ).prefetch_related(
            "items__product",
        ),
        pk=pk,
    )

    if order.status != SalesOrder.Status.DRAFT:
        messages.error(
            request,
            "Only a DRAFT sales order can be edited.",
        )

        return redirect(
            "sales_web:sales-order-detail",
            pk=order.pk,
        )

    if request.method == "POST":
        form = SalesOrderForm(
            request.POST,
            current_customer=(order.customer),
            current_warehouse=(order.warehouse),
        )

        item_formset = SalesOrderItemFormSet(
            request.POST,
            prefix="items",
        )

        if form.is_valid() and item_formset.is_valid():
            try:
                update_sales_order(
                    order_id=order.pk,
                    customer=(form.cleaned_data["customer"]),
                    warehouse=(form.cleaned_data["warehouse"]),
                    items=(_build_items_from_formset(item_formset)),
                )

            except SalesOrderServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )

            else:
                messages.success(
                    request,
                    "Sales order updated successfully.",
                )

                return redirect(
                    "sales_web:sales-order-detail",
                    pk=order.pk,
                )

    else:
        form = SalesOrderForm(
            initial={
                "customer": (order.customer),
                "warehouse": (order.warehouse),
            },
            current_customer=(order.customer),
            current_warehouse=(order.warehouse),
        )

        initial_items = [
            {
                "product": item.product,
                "quantity": (item.quantity),
                "unit_price": (item.unit_price),
            }
            for item in (order.items.all())
        ]

        item_formset = SalesOrderItemFormSet(
            initial=initial_items,
            prefix="items",
        )

    return render(
        request,
        "sales/orders/form.html",
        {
            "form": form,
            "item_formset": (item_formset),
            "order": order,
            "page_title": ("Edit Sales Order"),
            "page_subtitle": (f"Update {order.order_number}."),
            "submit_label": ("Save Changes"),
        },
    )


@login_required
def sales_order_confirm(
    request,
    pk,
):
    if not _can_manage_sales_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "sales_web:sales-order-detail",
            pk=pk,
        )

    try:
        confirm_sales_order(order_id=pk)

    except SalesOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Sales order confirmed successfully.",
        )

    return redirect(
        "sales_web:sales-order-detail",
        pk=pk,
    )


@login_required
def sales_order_cancel(
    request,
    pk,
):
    if not _can_manage_sales_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "sales_web:sales-order-detail",
            pk=pk,
        )

    try:
        cancel_sales_order(order_id=pk)

    except SalesOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Sales order cancelled.",
        )

    return redirect(
        "sales_web:sales-order-detail",
        pk=pk,
    )


@login_required
def sales_order_start_processing(
    request,
    pk,
):
    if not _can_process_sales_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "sales_web:sales-order-detail",
            pk=pk,
        )

    try:
        start_processing_sales_order(order_id=pk)

    except SalesOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Sales order moved to processing.",
        )

    return redirect(
        "sales_web:sales-order-detail",
        pk=pk,
    )


@login_required
def sales_order_ship(
    request,
    pk,
):
    if not _can_process_sales_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "sales_web:sales-order-detail",
            pk=pk,
        )

    try:
        ship_sales_order(
            order_id=pk,
            performed_by=request.user,
        )

    except SalesOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Sales order shipped successfully.",
        )

    return redirect(
        "sales_web:sales-order-detail",
        pk=pk,
    )
