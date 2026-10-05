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
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

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
