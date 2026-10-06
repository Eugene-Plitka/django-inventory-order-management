from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import (
    CanManagePurchaseOrder,
    CanReceivePurchaseOrder,
)

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer
from .services import (
    PurchaseOrderServiceError,
    cancel_purchase_order,
    confirm_purchase_order,
    receive_purchase_order,
)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.select_related(
        "supplier",
        "warehouse",
        "created_by",
    ).prefetch_related(
        "items__product",
    )
    serializer_class = PurchaseOrderSerializer

    filterset_fields = (
        "status",
        "supplier",
        "warehouse",
    )

    search_fields = (
        "order_number",
        "supplier__name",
    )

    ordering_fields = (
        "id",
        "order_number",
        "created_at",
        "confirmed_at",
        "received_at",
    )

    ordering = ("-created_at",)

    @extend_schema(
        request=None,
        responses=PurchaseOrderSerializer,
        description=(
            "Confirm a DRAFT purchase order. "
            "No stock quantity is changed at this stage."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanManagePurchaseOrder],
    )
    def confirm(self, request, pk=None):
        try:
            order = confirm_purchase_order(
                order_id=pk,
            )
        except PurchaseOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=PurchaseOrderSerializer,
        description=(
            "Receive a CONFIRMED purchase order, increase physical stock "
            "and create PURCHASE_RECEIPT stock movements."
        ),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanReceivePurchaseOrder],
    )
    def receive(self, request, pk=None):
        try:
            order = receive_purchase_order(
                order_id=pk,
                performed_by=request.user,
            )
        except PurchaseOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @extend_schema(
        request=None,
        responses=PurchaseOrderSerializer,
        description=("Cancel a DRAFT or CONFIRMED purchase order."),
    )
    @action(
        detail=True,
        methods=["post"],
        permission_classes=[CanManagePurchaseOrder],
    )
    def cancel(self, request, pk=None):
        try:
            order = cancel_purchase_order(
                order_id=pk,
            )
        except PurchaseOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)
