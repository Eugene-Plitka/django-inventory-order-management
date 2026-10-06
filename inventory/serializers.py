from rest_framework import serializers

from .models import Stock, StockMovement, Warehouse


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
    class Meta:
        model = Stock
        fields = (
            "id",
            "product",
            "warehouse",
            "quantity",
            "reorder_level",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


class StockAdjustmentSerializer(serializers.Serializer):
    quantity = serializers.IntegerField()
    reason = serializers.CharField()


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
