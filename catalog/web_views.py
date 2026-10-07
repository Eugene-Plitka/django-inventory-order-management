from django.contrib.auth.decorators import (
    login_required,
    permission_required,
)
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from core.pagination import get_items_per_page

from .forms import (
    CategoryForm,
    ManufacturerForm,
    ProductForm,
)
from .models import Category, Manufacturer, Product


@login_required
def product_list(request):
    products = Product.objects.select_related(
        "category",
        "manufacturer",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    category_id = request.GET.get(
        "category",
        "",
    ).strip()

    manufacturer_id = request.GET.get(
        "manufacturer",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "name",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        products = products.filter(
            Q(sku__icontains=search)
            | Q(name__icontains=search)
            | Q(description__icontains=search)
        )

    if category_id:
        products = products.filter(category_id=category_id)

    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)

    if status == "active":
        products = products.filter(is_active=True)

    if status == "inactive":
        products = products.filter(is_active=False)

    sort_fields = {
        "sku": "sku",
        "name": "name",
        "category": "category__name",
        "manufacturer": "manufacturer__name",
        "price": "sale_price",
        "status": "is_active",
    }

    sort_field = sort_fields.get(
        sort,
        "name",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    products = products.order_by(
        order_by,
        "id",
    )

    paginator = Paginator(
        products,
        get_items_per_page(),
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": (Category.objects.order_by("name")),
        "manufacturers": (Manufacturer.objects.order_by("name")),
        "search": search,
        "selected_category": category_id,
        "selected_manufacturer": manufacturer_id,
        "selected_status": status,
        "sort": sort,
        "direction": direction,
    }

    template_name = "catalog/products/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "catalog/products/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "catalog.add_product",
    raise_exception=True,
)
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("catalog_web:product-list")
    else:
        form = ProductForm()

    return render(
        request,
        "catalog/products/form.html",
        {
            "form": form,
            "page_title": "Add Product",
            "page_subtitle": ("Create a new product in the catalog."),
            "submit_label": "Create Product",
        },
    )


@login_required
@permission_required(
    "catalog.change_product",
    raise_exception=True,
)
def product_update(request, pk):
    product = get_object_or_404(
        Product,
        pk=pk,
    )

    if request.method == "POST":
        form = ProductForm(
            request.POST,
            instance=product,
        )

        if form.is_valid():
            form.save()

            return redirect("catalog_web:product-list")
    else:
        form = ProductForm(
            instance=product,
        )

    return render(
        request,
        "catalog/products/form.html",
        {
            "form": form,
            "product": product,
            "page_title": "Edit Product",
            "page_subtitle": (f"Update {product.sku} — {product.name}."),
            "submit_label": "Save Changes",
        },
    )


@login_required
def category_list(request):
    categories = Category.objects.all()

    search = request.GET.get(
        "search",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "name",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        categories = categories.filter(
            Q(name__icontains=search)
            | Q(slug__icontains=search)
            | Q(description__icontains=search)
        )

    sort_fields = {
        "name": "name",
        "slug": "slug",
    }

    sort_field = sort_fields.get(
        sort,
        "name",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    categories = categories.order_by(
        order_by,
        "id",
    )

    paginator = Paginator(
        categories,
        get_items_per_page(),
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
        "sort": sort,
        "direction": direction,
    }

    template_name = "catalog/categories/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "catalog/categories/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "catalog.add_category",
    raise_exception=True,
)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("catalog_web:category-list")
    else:
        form = CategoryForm()

    return render(
        request,
        "catalog/categories/form.html",
        {
            "form": form,
            "page_title": "Add Category",
            "page_subtitle": ("Create a new product category."),
            "submit_label": "Create Category",
        },
    )


@login_required
@permission_required(
    "catalog.change_category",
    raise_exception=True,
)
def category_update(request, pk):
    category = get_object_or_404(
        Category,
        pk=pk,
    )

    if request.method == "POST":
        form = CategoryForm(
            request.POST,
            instance=category,
        )

        if form.is_valid():
            form.save()

            return redirect("catalog_web:category-list")
    else:
        form = CategoryForm(
            instance=category,
        )

    return render(
        request,
        "catalog/categories/form.html",
        {
            "form": form,
            "category": category,
            "page_title": "Edit Category",
            "page_subtitle": (f"Update {category.name}."),
            "submit_label": "Save Changes",
        },
    )


@login_required
def manufacturer_list(request):
    manufacturers = Manufacturer.objects.all()

    search = request.GET.get(
        "search",
        "",
    ).strip()

    sort = request.GET.get(
        "sort",
        "name",
    ).strip()

    direction = request.GET.get(
        "direction",
        "asc",
    ).strip()

    if search:
        manufacturers = manufacturers.filter(
            Q(name__icontains=search)
            | Q(country__icontains=search)
            | Q(website__icontains=search)
        )

    sort_fields = {
        "name": "name",
        "country": "country",
        "website": "website",
    }

    sort_field = sort_fields.get(
        sort,
        "name",
    )

    if direction == "desc":
        order_by = f"-{sort_field}"
    else:
        direction = "asc"
        order_by = sort_field

    manufacturers = manufacturers.order_by(
        order_by,
        "id",
    )

    paginator = Paginator(
        manufacturers,
        get_items_per_page(),
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "search": search,
        "sort": sort,
        "direction": direction,
    }

    template_name = "catalog/manufacturers/list.html"

    if request.headers.get("HX-Request") == "true":
        template_name = "catalog/manufacturers/_table.html"

    return render(
        request,
        template_name,
        context,
    )


@login_required
@permission_required(
    "catalog.add_manufacturer",
    raise_exception=True,
)
def manufacturer_create(request):
    if request.method == "POST":
        form = ManufacturerForm(request.POST)

        if form.is_valid():
            form.save()

            return redirect("catalog_web:manufacturer-list")
    else:
        form = ManufacturerForm()

    return render(
        request,
        "catalog/manufacturers/form.html",
        {
            "form": form,
            "page_title": "Add Manufacturer",
            "page_subtitle": ("Create a new product manufacturer."),
            "submit_label": "Create Manufacturer",
        },
    )


@login_required
@permission_required(
    "catalog.change_manufacturer",
    raise_exception=True,
)
def manufacturer_update(request, pk):
    manufacturer = get_object_or_404(
        Manufacturer,
        pk=pk,
    )

    if request.method == "POST":
        form = ManufacturerForm(
            request.POST,
            instance=manufacturer,
        )

        if form.is_valid():
            form.save()

            return redirect("catalog_web:manufacturer-list")
    else:
        form = ManufacturerForm(
            instance=manufacturer,
        )

    return render(
        request,
        "catalog/manufacturers/form.html",
        {
            "form": form,
            "manufacturer": manufacturer,
            "page_title": "Edit Manufacturer",
            "page_subtitle": (f"Update {manufacturer.name}."),
            "submit_label": "Save Changes",
        },
    )
