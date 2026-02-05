from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Order, OrderItem
from .serializers import OrderCreateSerializer, OrderReadSerializer
from product.models import Product


class OrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    # POST /api/orders/  → 주문 생성
    @transaction.atomic
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data["items"]

        if not items:
            return Response(
                {"message": "빈 장바구니로는 주문할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        order = Order.objects.create(user=request.user)

        for item in items:
            product = Product.objects.get(id=item["product_id"])

            OrderItem.objects.create(
                order=order,
                product=product,
                price=product.price,     # 주문 시점 가격 스냅샷
                quantity=item["quantity"],
            )

        return Response(
            {
                "order_id": order.id,
                "status": order.status,
            },
            status=status.HTTP_201_CREATED,
        )

    # GET /api/orders/  → 주문 목록 조회
    def get(self, request):
        orders = Order.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = OrderReadSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
