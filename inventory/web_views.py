from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from core.pagination import get_items_per_page

from .forms import (
    StockAdjustmentForm,
    WarehouseForm,
)
from .models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)
from .services import (
    StockServiceError,
    adjust_stock,
)


def _user_is_administrator(user):
    return user.is_superuser or user.groups.filter(name="Administrator").exists()


@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()

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
        "code",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        warehouses = warehouses.filter(
            Q(name__icontains=search)
            | Q(code__icontains=search)
            | Q(address__icontains=search)
        )

    if status == "active":
        warehouses = warehouses.filter(is_active=True)

    if status == "inactive":
        warehouses = warehouses.filter(is_active=False)

    sort_fields = {
        "code": "code",
        "name": "name",
        "address": "address",
        "status": "is_active",
        "updated": "updated_at",
    }

    sort_field = sort_fields.get(
        sort,
        "code",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    warehouses = warehouses.order_by(
        order_by,
        "id",
    )

    paginator = Paginator(
        warehouses,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "sort": sort,
        "direction": direction,
    }

    template_name = "inventory/warehouses/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "inventory/warehouses/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "inventory.view_stock",
    raise_exception=True,
)
def stock_list(request):
    stocks = (
        Stock.objects.select_related(
            "product",
            "product__category",
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

    search = request.GET.get(
        "search",
        "",
    ).strip()

    warehouse_id = request.GET.get(
        "warehouse",
        "",
    ).strip()

    low_stock = request.GET.get(
        "low_stock",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "product",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        stocks = stocks.filter(
            Q(product__sku__icontains=search) | Q(product__name__icontains=search)
        )

    if warehouse_id:
        stocks = stocks.filter(warehouse_id=warehouse_id)

    if low_stock == "true":
        stocks = stocks.filter(available_quantity__lte=F("reorder_level"))

    sort_fields = {
        "sku": "product__sku",
        "product": "product__name",
        "warehouse": "warehouse__code",
        "physical": "quantity",
        "reserved": "reserved_quantity",
        "available": "available_quantity",
        "reorder": "reorder_level",
    }

    sort_field = sort_fields.get(
        sort,
        "product__name",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    stocks = stocks.order_by(
        order_by,
        "warehouse__code",
        "id",
    )

    paginator = Paginator(
        stocks,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "warehouses": (Warehouse.objects.filter(is_active=True).order_by("code")),
        "search": search,
        "selected_warehouse": warehouse_id,
        "selected_low_stock": low_stock,
        "sort": sort,
        "direction": direction,
        "is_administrator": (_user_is_administrator(request.user)),
    }

    template_name = "inventory/stock/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "inventory/stock/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "inventory.view_stock",
    raise_exception=True,
)
def stock_adjust(request, pk):
    if not _user_is_administrator(request.user):
        from django.core.exceptions import (
            PermissionDenied,
        )

        raise PermissionDenied

    stock = get_object_or_404(
        Stock.objects.select_related(
            "product",
            "warehouse",
        ),
        pk=pk,
    )

    if request.method == "POST":
        form = StockAdjustmentForm(request.POST)

        if form.is_valid():
            try:
                adjust_stock(
                    stock_id=stock.id,
                    quantity=form.cleaned_data["quantity"],
                    reason=form.cleaned_data["reason"],
                    performed_by=request.user,
                )
            except StockServiceError as exc:
                form.add_error(
                    None,
                    str(exc),
                )
            else:
                return redirect("inventory_web:stock-list")
    else:
        form = StockAdjustmentForm()

    return render(
        request,
        "inventory/stock/adjust.html",
        {
            "form": form,
            "stock": stock,
        },
    )


@login_required
@permission_required(
    "inventory.add_warehouse",
    raise_exception=True,
)
def warehouse_create(request):
    if request.method == "POST":
        form = WarehouseForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("inventory_web:warehouse-list")
    else:
        form = WarehouseForm()

    return render(
        request,
        "inventory/warehouses/form.html",
        {
            "form": form,
            "page_title": "Add Warehouse",
            "page_subtitle": ("Create a new inventory warehouse."),
            "submit_label": "Create Warehouse",
        },
    )


@login_required
@permission_required(
    "inventory.change_warehouse",
    raise_exception=True,
)
def warehouse_update(request, pk):
    warehouse = get_object_or_404(
        Warehouse,
        pk=pk,
    )

    if request.method == "POST":
        form = WarehouseForm(
            request.POST,
            instance=warehouse,
        )

        if form.is_valid():
            form.save()

            return redirect("inventory_web:warehouse-list")
    else:
        form = WarehouseForm(instance=warehouse)

    return render(
        request,
        "inventory/warehouses/form.html",
        {
            "form": form,
            "warehouse": warehouse,
            "page_title": "Edit Warehouse",
            "page_subtitle": (f"Update {warehouse.code} — {warehouse.name}."),
            "submit_label": "Save Changes",
        },
    )


@login_required
@permission_required(
    "inventory.view_stockreservation",
    raise_exception=True,
)
def reservation_list(request):
    reservations = StockReservation.objects.select_related(
        "stock",
        "stock__product",
        "stock__warehouse",
        "sales_order_item",
        "sales_order_item__sales_order",
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
        reservations = reservations.filter(
            Q(stock__product__sku__icontains=search)
            | Q(stock__product__name__icontains=search)
            | Q(stock__warehouse__code__icontains=search)
            | Q(sales_order_item__sales_order__order_number__icontains=search)
        )

    if status:
        reservations = reservations.filter(status=status)

    sort_fields = {
        "order": ("sales_order_item__sales_order__order_number"),
        "sku": "stock__product__sku",
        "product": "stock__product__name",
        "warehouse": "stock__warehouse__code",
        "quantity": "quantity",
        "status": "status",
        "created": "created_at",
        "released": "released_at",
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

    reservations = reservations.order_by(
        order_by,
        "-id",
    )

    paginator = Paginator(
        reservations,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
        "statuses": (StockReservation.Status.choices),
        "sort": sort,
        "direction": direction,
    }

    template_name = "inventory/reservations/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "inventory/reservations/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "inventory.view_stockmovement",
    raise_exception=True,
)
def movement_list(request):
    movements = StockMovement.objects.select_related(
        "stock",
        "stock__product",
        "stock__warehouse",
        "performed_by",
        "sales_order_item",
        "purchase_order_item",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    movement_type = request.GET.get(
        "movement_type",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "date",
    ).strip()

    direction = request.GET.get(
        "direction",
        "desc",
    ).strip()

    if search:
        movements = movements.filter(
            Q(stock__product__sku__icontains=search)
            | Q(stock__product__name__icontains=search)
            | Q(stock__warehouse__code__icontains=search)
            | Q(reason__icontains=search)
            | Q(performed_by__email__icontains=search)
        )

    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    sort_fields = {
        "date": "created_at",
        "sku": "stock__product__sku",
        "product": "stock__product__name",
        "warehouse": "stock__warehouse__code",
        "type": "movement_type",
        "quantity": "quantity",
        "performed_by": "performed_by__email",
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

    movements = movements.order_by(
        order_by,
        "-id",
    )

    paginator = Paginator(
        movements,
        get_items_per_page(),
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "search": search,
        "selected_movement_type": (movement_type),
        "movement_types": (StockMovement.MovementType.choices),
        "sort": sort,
        "direction": direction,
    }

    template_name = "inventory/movements/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "inventory/movements/_table.html"

    return render(
        request,
        template_name,
        context,
    )
