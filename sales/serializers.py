from rest_framework import serializers
from decimal import Decimal

from .models import SalesOrder, SalesOrderItem
from .services import (
    create_sales_order,
    update_sales_order,
)


class SalesOrderItemSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(
        min_value=1,
    )

    unit_price = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0"),
    )

    class Meta:
        model = SalesOrderItem
        fields = (
            "id",
            "product",
            "quantity",
            "unit_price",
        )
        read_only_fields = ("id",)


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True)

    class Meta:
        model = SalesOrder
        fields = (
            "id",
            "order_number",
            "customer",
            "warehouse",
            "status",
            "created_by",
            "created_at",
            "confirmed_at",
            "shipped_at",
            "cancelled_at",
            "items",
        )

        read_only_fields = (
            "id",
            "order_number",
            "status",
            "created_by",
            "created_at",
            "confirmed_at",
            "shipped_at",
            "cancelled_at",
        )

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError(
                "Sales order must contain at least one item."
            )

        product_ids = [item["product"].id for item in value]

        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError(
                "Sales order cannot contain duplicate products."
            )

        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        request = self.context["request"]

        return create_sales_order(
            created_by=request.user,
            items=items_data,
            **validated_data,
        )

    def update(self, instance, validated_data):
        items_data = validated_data.pop(
            "items",
            None,
        )

        return update_sales_order(
            order_id=instance.id,
            items=items_data,
            **validated_data,
        )
