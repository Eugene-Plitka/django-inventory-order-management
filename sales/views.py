from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

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
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            order = confirm_sales_order(
                order_id=pk,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        try:
            order = cancel_sales_order(
                order_id=pk,
            )
        except SalesOrderServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        serializer = self.get_serializer(order)

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="start-processing",
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

    @action(detail=True, methods=["post"])
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
