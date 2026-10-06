from rest_framework import serializers

from .models import PurchaseOrder, PurchaseOrderItem
from .services import create_purchase_order


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseOrderItem
        fields = (
            "id",
            "product",
            "quantity",
            "unit_price",
        )
        read_only_fields = ("id",)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True)

    class Meta:
        model = PurchaseOrder
        fields = (
            "id",
            "order_number",
            "supplier",
            "warehouse",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "confirmed_at",
            "received_at",
            "cancelled_at",
            "items",
        )
        read_only_fields = (
            "id",
            "order_number",
            "status",
            "created_by",
            "created_at",
            "updated_at",
            "confirmed_at",
            "received_at",
            "cancelled_at",
        )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Purchase order must contain at least one item."
            )

        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context["request"]

        return create_purchase_order(
            created_by=request.user,
            items=items_data,
            **validated_data,
        )
