from rest_framework import serializers
from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="product.id")
    product_name = serializers.CharField(source="product.product_name")
    price = serializers.IntegerField(source="product.price")

    class Meta:
        model = CartItem
        fields = [
            "product_id",
            "product_name",
            "price",
            "quantity",
        ]


class CartSerializer(serializers.ModelSerializer):
    cart_id = serializers.IntegerField(source="id")
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = [
            "cart_id",
            "items",
        ]


class CartItemCreateSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
