from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import PurchaseOrder
from .serializers import PurchaseOrderSerializer
from .services import (
    PurchaseOrderServiceError,
    confirm_purchase_order,
    receive_purchase_order,
)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            order = confirm_purchase_order(
                order_id=pk,
            )
        except PurchaseOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
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
