from rest_framework import serializers
from .models import Order, OrderItem
from product.models import Product


class OrderItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    items = OrderItemCreateSerializer(many=True)


class OrderItemReadSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.product_name"
    )
    brand = serializers.CharField(source="product.brand")
    image_url = serializers.CharField(
        source="product.product_image_path"
    )

    class Meta:
        model = OrderItem
        fields = [
            "product_name",
            "brand",
            "price",
            "quantity",
            "image_url",
        ]


class OrderReadSerializer(serializers.ModelSerializer):
    total_price = serializers.SerializerMethodField()
    total_quantity = serializers.SerializerMethodField()
    items = OrderItemReadSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "status",
            "total_price",
            "total_quantity",
            "created_at",
            "items",
        ]

    def get_total_price(self, obj):
        return obj.total_price()

    def get_total_quantity(self, obj):
        return obj.total_quantity()
