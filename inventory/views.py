from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Stock, Warehouse
from .permissions import IsAdministrator
from .serializers import (
    StockAdjustmentSerializer,
    StockSerializer,
    WarehouseSerializer,
)
from .services import StockServiceError, adjust_stock


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer


class StockViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAdministrator],
    )
    def adjust(self, request, pk=None):
        input_serializer = StockAdjustmentSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            stock = adjust_stock(
                stock_id=pk,
                quantity=input_serializer.validated_data["quantity"],
                reason=input_serializer.validated_data["reason"],
                performed_by=request.user,
            )
        except StockServiceError as exc:
            raise ValidationError({"detail": str(exc)})

        output_serializer = self.get_serializer(stock)

        return Response(output_serializer.data)
