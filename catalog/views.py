from rest_framework import viewsets

from .models import Category, Manufacturer, Product
from .serializers import (
    CategorySerializer,
    ManufacturerSerializer,
    ProductSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    search_fields = (
        "name",
        "slug",
    )

    ordering_fields = (
        "id",
        "name",
        "created_at",
    )

    ordering = ("name",)


class ManufacturerViewSet(viewsets.ModelViewSet):
    queryset = Manufacturer.objects.all()
    serializer_class = ManufacturerSerializer

    search_fields = (
        "name",
        "country",
    )

    ordering_fields = (
        "id",
        "name",
        "created_at",
    )

    ordering = ("name",)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related(
        "category",
        "manufacturer",
    )
    serializer_class = ProductSerializer

    filterset_fields = (
        "category",
        "manufacturer",
        "is_active",
    )

    search_fields = (
        "sku",
        "name",
        "description",
    )

    ordering_fields = (
        "id",
        "sku",
        "name",
        "sale_price",
        "created_at",
    )

    ordering = ("name",)
