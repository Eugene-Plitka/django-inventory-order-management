from rest_framework import serializers

from .models import (
    Stock,
    StockMovement,
    StockReservation,
    Warehouse,
)


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = (
            "id",
            "name",
            "code",
            "address",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class StockSerializer(serializers.ModelSerializer):
    reserved_quantity = serializers.IntegerField(read_only=True)

    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = Stock
        fields = (
            "id",
            "product",
            "warehouse",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "reorder_level",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "created_at",
            "updated_at",
        )


class StockAdjustmentSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    reason = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

    def validate_quantity(self, value):
        if value == 0:
            raise serializers.ValidationError("Quantity must not be zero.")

        return value


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = (
            "id",
            "stock",
            "movement_type",
            "quantity",
            "sales_order_item",
            "purchase_order_item",
            "reason",
            "performed_by",
            "created_at",
        )
        read_only_fields = fields


class StockReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReservation
        fields = (
            "id",
            "sales_order_item",
            "stock",
            "quantity",
            "status",
            "created_at",
            "released_at",
        )
        read_only_fields = fields
