import uuid
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import Payment
from .serializers import (
    PaymentPrepareSerializer,
    PaymentConfirmSerializer,
    PaymentListSerializer,
)
from order.models import Order


class PaymentPrepareView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentPrepareSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order_id = serializer.validated_data["order_id"]
        order = Order.objects.select_for_update().get(id=order_id)

        if order.user != request.user:
            return Response(
                {"message": "본인의 주문만 결제할 수 있습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        total_price = order.total_price()

        if total_price <= 0:
            return Response(
                {"message": "결제 금액이 유효하지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_key = f"payment_{uuid.uuid4().hex[:20]}"
        payment = Payment.objects.create(
            order=order,
            payment_key=payment_key,
            price=total_price,
            status=Payment.Status.PENDING,
        )

        response_serializer = PaymentPrepareSerializer({
            "payment_key": payment.payment_key,
            "price": payment.price,
        })

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class PaymentConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]  # Toss 서버에서 호출하므로
    serializer_class = PaymentConfirmSerializer

    @transaction.atomic
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {"message": "Webhook 검증 실패", "detail": str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        payment = serializer.validated_data["payment"]
        order = serializer.validated_data["order"]

        # TODO: 실제 환경에서는 Toss API로 결제 승인 요청
        # import requests
        # toss_response = requests.post(
        #     "https://api.tosspayments.com/v1/payments/confirm",
        #     headers={"Authorization": f"Basic {TOSS_SECRET_KEY}"},
        #     json={"paymentKey": payment.payment_key, "orderId": order.id, "amount": payment.price}
        # )
        # if toss_response.status_code != 200:
        #     return Response({"message": "Toss 결제 실패"}, status=400)

        # Payment 상태 업데이트
        payment.status = Payment.Status.PAID
        payment.paid_at = timezone.now()
        payment.save()

        # Order 상태 업데이트
        order.status = Order.Status.PAID
        order.save()

        response_serializer = PaymentConfirmSerializer({
            "status": payment.status,
        })

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class PaymentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PaymentListSerializer

    def get_queryset(self):
        return Payment.objects.filter(
            order__user=self.request.user
        ).select_related("order").order_by("-created_at")
