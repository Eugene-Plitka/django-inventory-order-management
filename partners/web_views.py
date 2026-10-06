from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import CustomerForm, SupplierForm
from .models import Customer, Supplier


def _partner_list_context(request, queryset):
    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search)
            | Q(contact_person__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(tax_id__icontains=search)
        )

    if status == "active":
        queryset = queryset.filter(is_active=True)

    if status == "inactive":
        queryset = queryset.filter(is_active=False)

    queryset = queryset.order_by("name")

    paginator = Paginator(
        queryset,
        20,
    )

    page_obj = paginator.get_page(request.GET.get("page"))

    return {
        "page_obj": page_obj,
        "search": search,
        "selected_status": status,
    }


@login_required
def customer_list(request):
    context = _partner_list_context(
        request,
        Customer.objects.all(),
    )

    template_name = "partners/customers/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "partners/customers/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "partners.add_customer",
    raise_exception=True,
)
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("partners_web:customer-list")
    else:
        form = CustomerForm()

    return render(
        request,
        "partners/customers/form.html",
        {
            "form": form,
            "page_title": "Add Customer",
            "page_subtitle": ("Create a new customer company."),
            "submit_label": "Create Customer",
        },
    )


@login_required
@permission_required(
    "partners.change_customer",
    raise_exception=True,
)
def customer_update(request, pk):
    customer = get_object_or_404(
        Customer,
        pk=pk,
    )

    if request.method == "POST":
        form = CustomerForm(
            request.POST,
            instance=customer,
        )

        if form.is_valid():
            form.save()

            return redirect("partners_web:customer-list")
    else:
        form = CustomerForm(instance=customer)

    return render(
        request,
        "partners/customers/form.html",
        {
            "form": form,
            "customer": customer,
            "page_title": "Edit Customer",
            "page_subtitle": (f"Update {customer.name}."),
            "submit_label": "Save Changes",
        },
    )


@login_required
def supplier_list(request):
    context = _partner_list_context(
        request,
        Supplier.objects.all(),
    )

    template_name = "partners/suppliers/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "partners/suppliers/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "partners.add_supplier",
    raise_exception=True,
)
def supplier_create(request):
    if request.method == "POST":
        form = SupplierForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("partners_web:supplier-list")
    else:
        form = SupplierForm()

    return render(
        request,
        "partners/suppliers/form.html",
        {
            "form": form,
            "page_title": "Add Supplier",
            "page_subtitle": ("Create a new supplier company."),
            "submit_label": "Create Supplier",
        },
    )


@login_required
@permission_required(
    "partners.change_supplier",
    raise_exception=True,
)
def supplier_update(request, pk):
    supplier = get_object_or_404(
        Supplier,
        pk=pk,
    )

    if request.method == "POST":
        form = SupplierForm(
            request.POST,
            instance=supplier,
        )

        if form.is_valid():
            form.save()

            return redirect("partners_web:supplier-list")
    else:
        form = SupplierForm(instance=supplier)

    return render(
        request,
        "partners/suppliers/form.html",
        {
            "form": form,
            "supplier": supplier,
            "page_title": "Edit Supplier",
            "page_subtitle": (f"Update {supplier.name}."),
            "submit_label": "Save Changes",
        },
    )
