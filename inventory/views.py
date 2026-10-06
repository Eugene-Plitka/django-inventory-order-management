from django.db.models import F, Q, Sum, Value
from django.db.models.functions import Coalesce

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)
from .permissions import IsAdministrator
from .serializers import (
    StockAdjustmentSerializer,
    StockMovementSerializer,
    StockReservationSerializer,
    StockSerializer,
    WarehouseSerializer,
)
from .services import StockServiceError, adjust_stock


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

    filterset_fields = ("is_active",)

    search_fields = (
        "code",
        "name",
        "address",
    )

    ordering_fields = (
        "id",
        "code",
        "name",
        "created_at",
    )

    ordering = ("code",)


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = (
        Stock.objects.select_related(
            "product",
            "warehouse",
        )
        .annotate(
            reserved_quantity=Coalesce(
                Sum(
                    "reservations__quantity",
                    filter=Q(reservations__status=StockReservation.Status.ACTIVE),
                ),
                Value(0),
            )
        )
        .annotate(available_quantity=F("quantity") - F("reserved_quantity"))
    )

    serializer_class = StockSerializer

    filterset_fields = (
        "product",
        "warehouse",
    )

    search_fields = (
        "product__sku",
        "product__name",
        "warehouse__code",
        "warehouse__name",
    )

    ordering_fields = (
        "id",
        "quantity",
        "reorder_level",
        "updated_at",
    )

    ordering = ("id",)

    def get_queryset(self):
        queryset = super().get_queryset()

        low_stock = self.request.query_params.get("low_stock")

        if low_stock is None:
            return queryset

        low_stock = low_stock.lower()

        if low_stock == "true":
            return queryset.filter(available_quantity__lte=F("reorder_level"))

        if low_stock == "false":
            return queryset.filter(available_quantity__gt=F("reorder_level"))

        raise ValidationError({"low_stock": ("Value must be 'true' or 'false'.")})

    @extend_schema(
        request=StockAdjustmentSerializer,
        responses=StockSerializer,
        description=(
            "Manually adjust physical stock. "
            "Only administrators can perform this operation. "
            "A StockMovement is created automatically."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrator],
    )
    def adjust(self, request, pk=None):
        serializer = StockAdjustmentSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        try:
            stock = adjust_stock(
                stock_id=pk,
                quantity=serializer.validated_data["quantity"],
                reason=serializer.validated_data["reason"],
                performed_by=request.user,
            )
        except StockServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        output_serializer = StockSerializer(
            stock,
            context=self.get_serializer_context(),
        )

        return Response(output_serializer.data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related(
        "stock",
        "stock__product",
        "stock__warehouse",
        "performed_by",
        "sales_order_item",
        "purchase_order_item",
    )
    serializer_class = StockMovementSerializer

    filterset_fields = (
        "stock",
        "movement_type",
        "performed_by",
    )

    search_fields = (
        "stock__product__sku",
        "stock__product__name",
        "stock__warehouse__code",
        "stock__warehouse__name",
        "reason",
    )

    ordering_fields = (
        "id",
        "quantity",
        "created_at",
    )

    ordering = ("-created_at",)


class StockReservationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockReservation.objects.select_related(
        "stock",
        "stock__product",
        "stock__warehouse",
        "sales_order_item",
        "sales_order_item__sales_order",
        "sales_order_item__product",
    )

    serializer_class = StockReservationSerializer

    filterset_fields = (
        "stock",
        "status",
        "sales_order_item",
    )

    search_fields = (
        "stock__product__sku",
        "stock__product__name",
        "stock__warehouse__code",
        "stock__warehouse__name",
        "sales_order_item__sales_order__order_number",
    )

    ordering_fields = (
        "id",
        "quantity",
        "created_at",
        "released_at",
    )

    ordering = ("-created_at",)
