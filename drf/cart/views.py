from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    CartItemCreateSerializer,
)
from product.models import Product


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CartItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = get_object_or_404(
            Product,
            id=serializer.validated_data["product_id"]
        )
        quantity = serializer.validated_data["quantity"]

        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                "user": request.user,
                "quantity": quantity,
            }
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return Response(
            {"message": "added"},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, product_id):
        cart = get_object_or_404(Cart, user=request.user)

        cart_item = get_object_or_404(
            CartItem,
            cart=cart,
            product_id=product_id
        )
        cart_item.delete()

        return Response(
            {"message": "deleted"},
            status=status.HTTP_200_OK
        )
