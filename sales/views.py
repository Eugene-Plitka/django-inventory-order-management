from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import (
    CanManageSalesOrder,
    CanProcessSalesOrder,
)

from .exceptions import SalesOrderServiceError
from .models import SalesOrder
from .serializers import SalesOrderSerializer
from .services import (
    cancel_sales_order,
    confirm_sales_order,
    ship_sales_order,
    start_processing_sales_order,
)


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.select_related(
        "customer",
        "warehouse",
        "created_by",
    ).prefetch_related(
        "items__product",
    )

    serializer_class = SalesOrderSerializer

    http_method_names = (
        "get",
        "post",
        "put",
        "patch",
        "head",
        "options",
    )

    filterset_fields = (
        "status",
        "customer",
        "warehouse",
    )

    search_fields = (
        "order_number",
        "customer__name",
    )

    ordering_fields = (
        "id",
        "order_number",
        "created_at",
        "confirmed_at",
        "shipped_at",
    )

    ordering = ("-created_at",)

    def update(self, request, *args, **kwargs):
        try:
            return super().update(
                request,
                *args,
                **kwargs,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

    @extend_schema(
        request=None,
        responses=SalesOrderSerializer,
        description=(
            "Confirm a DRAFT sales order and create active stock reservations."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanManageSalesOrder],
    )
    def confirm(self, request, pk=None):
        try:
            order = confirm_sales_order(
                order_id=pk,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=SalesOrderSerializer,
        description=(
            "Cancel a DRAFT or CONFIRMED sales order. "
            "Active reservations are released when required."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanManageSalesOrder],
    )
    def cancel(self, request, pk=None):
        try:
            order = cancel_sales_order(
                order_id=pk,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=SalesOrderSerializer,
        description=("Move a CONFIRMED sales order to PROCESSING."),
    )
    @action(
        detail=True,
        methods=["post"],
        url_path="start-processing",
        permission_classes=[CanProcessSalesOrder],
    )
    def start_processing(self, request, pk=None):
        try:
            order = start_processing_sales_order(
                order_id=pk,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=SalesOrderSerializer,
        description=(
            "Ship a PROCESSING sales order, decrease physical stock, "
            "consume active reservations and create "
            "SALES_SHIPMENT stock movements."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanProcessSalesOrder],
    )
    def ship(self, request, pk=None):
        try:
            order = ship_sales_order(
                order_id=pk,
                performed_by=request.user,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)
