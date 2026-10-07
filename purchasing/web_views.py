from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Q,
    Sum,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from core.pagination import get_items_per_page

from .forms import (
    PurchaseOrderForm,
    PurchaseOrderItemFormSet,
)
from .models import PurchaseOrder
from .services import (
    PurchaseOrderServiceError,
    cancel_purchase_order,
    confirm_purchase_order,
    create_purchase_order,
    receive_purchase_order,
    update_purchase_order,
)


def _has_role(user, *roles):
    if user.is_superuser:
        return True

    return user.groups.filter(name__in=roles).exists()


def _can_manage_purchase_order(user):
    return _has_role(
        user,
        "Administrator",
        "Purchasing Manager",
    )


def _can_receive_purchase_order(user):
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
    "purchasing.view_purchaseorder",
    raise_exception=True,
)
def purchase_order_list(request):
    line_total_expression = ExpressionWrapper(
        F("items__quantity") * F("items__unit_price"),
        output_field=DecimalField(
            max_digits=14,
            decimal_places=2,
        ),
    )

    orders = (
        PurchaseOrder.objects.select_related(
            "supplier",
            "warehouse",
            "created_by",
        )
        .prefetch_related(
            "items",
        )
        .annotate(total_amount=Sum(line_total_expression))
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "created",
    ).strip()

    direction = request.GET.get(
        "direction",
        "desc",
    ).strip()

    if search:
        orders = orders.filter(
            Q(order_number__icontains=search)
            | Q(supplier__name__icontains=search)
            | Q(warehouse__code__icontains=search)
        )

    if status:
        orders = orders.filter(status=status)

    sort_fields = {
        "order": "order_number",
        "supplier": "supplier__name",
        "warehouse": "warehouse__code",
        "total": "total_amount",
        "status": "status",
        "created": "created_at",
    }

    sort_field = sort_fields.get(
        sort,
        "created_at",
    )

    if direction == "asc":
        order_by = sort_field
    else:
        direction = "desc"
        order_by = f"-{sort_field}"

    orders = orders.order_by(
        order_by,
        "-id",
    )

    paginator = Paginator(
        orders,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "statuses": PurchaseOrder.Status.choices,
        "sort": sort,
        "direction": direction,
        "can_manage_purchase": (_can_manage_purchase_order(request.user)),
    }

    template_name = "purchasing/orders/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "purchasing/orders/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "purchasing.add_purchaseorder",
    raise_exception=True,
)
def purchase_order_create(request):
    if not _can_manage_purchase_order(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = PurchaseOrderForm(request.POST)

        item_formset = PurchaseOrderItemFormSet(
            request.POST,
            prefix="items",
        )

        if form.is_valid() and item_formset.is_valid():
            order = create_purchase_order(
                created_by=request.user,
                supplier=form.cleaned_data["supplier"],
                warehouse=form.cleaned_data["warehouse"],
                items=_build_items_from_formset(item_formset),
            )

            messages.success(
                request,
                "Purchase order created successfully.",
            )

            return redirect(
                "purchasing_web:purchase-order-detail",
                pk=order.pk,
            )

    else:
        form = PurchaseOrderForm()

        item_formset = PurchaseOrderItemFormSet(
            prefix="items",
        )

    return render(
        request,
        "purchasing/orders/form.html",
        {
            "form": form,
            "item_formset": item_formset,
            "page_title": "New Purchase Order",
            "page_subtitle": ("Create a draft supplier purchase order."),
            "submit_label": "Create Order",
        },
    )


@login_required
@permission_required(
    "purchasing.view_purchaseorder",
    raise_exception=True,
)
def purchase_order_detail(
    request,
    pk,
):
    order = get_object_or_404(
        PurchaseOrder.objects.select_related(
            "supplier",
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

    can_manage = _can_manage_purchase_order(request.user)

    can_receive = _can_receive_purchase_order(request.user)

    context = {
        "order": order,
        "items": items,
        "order_total": order_total,
        "can_edit": (can_manage and order.status == PurchaseOrder.Status.DRAFT),
        "can_confirm": (can_manage and order.status == PurchaseOrder.Status.DRAFT),
        "can_cancel": (
            can_manage
            and order.status
            in {
                PurchaseOrder.Status.DRAFT,
                PurchaseOrder.Status.CONFIRMED,
            }
        ),
        "can_receive": (can_receive and order.status == PurchaseOrder.Status.CONFIRMED),
    }

    return render(
        request,
        "purchasing/orders/detail.html",
        context,
    )


@login_required
@permission_required(
    "purchasing.change_purchaseorder",
    raise_exception=True,
)
def purchase_order_update(
    request,
    pk,
):
    if not _can_manage_purchase_order(request.user):
        raise PermissionDenied

    order = get_object_or_404(
        PurchaseOrder.objects.select_related(
            "supplier",
            "warehouse",
        ).prefetch_related(
            "items__product",
        ),
        pk=pk,
    )

    if order.status != PurchaseOrder.Status.DRAFT:
        messages.error(
            request,
            "Only a DRAFT purchase order can be edited.",
        )

        return redirect(
            "purchasing_web:purchase-order-detail",
            pk=order.pk,
        )

    if request.method == "POST":
        form = PurchaseOrderForm(
            request.POST,
            current_supplier=order.supplier,
            current_warehouse=order.warehouse,
        )

        item_formset = PurchaseOrderItemFormSet(
            request.POST,
            prefix="items",
        )

        if form.is_valid() and item_formset.is_valid():
            try:
                update_purchase_order(
                    order_id=order.pk,
                    supplier=form.cleaned_data["supplier"],
                    warehouse=form.cleaned_data["warehouse"],
                    items=_build_items_from_formset(item_formset),
                )

            except PurchaseOrderServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )

            else:
                messages.success(
                    request,
                    "Purchase order updated successfully.",
                )

                return redirect(
                    "purchasing_web:purchase-order-detail",
                    pk=order.pk,
                )

    else:
        form = PurchaseOrderForm(
            initial={
                "supplier": order.supplier,
                "warehouse": order.warehouse,
            },
            current_supplier=order.supplier,
            current_warehouse=order.warehouse,
        )

        initial_items = [
            {
                "product": item.product,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in order.items.all()
        ]

        item_formset = PurchaseOrderItemFormSet(
            initial=initial_items,
            prefix="items",
        )

    return render(
        request,
        "purchasing/orders/form.html",
        {
            "form": form,
            "item_formset": item_formset,
            "order": order,
            "page_title": "Edit Purchase Order",
            "page_subtitle": (f"Update {order.order_number}."),
            "submit_label": "Save Changes",
        },
    )


@login_required
def purchase_order_confirm(
    request,
    pk,
):
    if not _can_manage_purchase_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "purchasing_web:purchase-order-detail",
            pk=pk,
        )

    try:
        confirm_purchase_order(order_id=pk)

    except PurchaseOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Purchase order confirmed successfully.",
        )

    return redirect(
        "purchasing_web:purchase-order-detail",
        pk=pk,
    )


@login_required
def purchase_order_cancel(
    request,
    pk,
):
    if not _can_manage_purchase_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "purchasing_web:purchase-order-detail",
            pk=pk,
        )

    try:
        cancel_purchase_order(order_id=pk)

    except PurchaseOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Purchase order cancelled.",
        )

    return redirect(
        "purchasing_web:purchase-order-detail",
        pk=pk,
    )


@login_required
def purchase_order_receive(
    request,
    pk,
):
    if not _can_receive_purchase_order(request.user):
        raise PermissionDenied

    if request.method != "POST":
        return redirect(
            "purchasing_web:purchase-order-detail",
            pk=pk,
        )

    try:
        receive_purchase_order(
            order_id=pk,
            performed_by=request.user,
        )

    except PurchaseOrderServiceError as exc:
        messages.error(
            request,
            str(exc),
        )

    else:
        messages.success(
            request,
            "Purchase order received successfully.",
        )

    return redirect(
        "purchasing_web:purchase-order-detail",
        pk=pk,
    )
