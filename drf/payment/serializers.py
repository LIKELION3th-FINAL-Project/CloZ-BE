from rest_framework import serializers
from .models import Payment
from order.models import Order


class PaymentPrepareSerializer(serializers.Serializer):
    # 요청 필드
    order_id = serializers.IntegerField(write_only=True)

    # 응답 필드
    payment_key = serializers.CharField(read_only=True)
    price = serializers.IntegerField(read_only=True)

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 주문입니다.")

        # 주문 상태 확인
        if order.status != Order.Status.PENDING:
            raise serializers.ValidationError("결제 가능한 상태가 아닙니다.")

        # 이미 결제가 생성되었는지 확인
        if hasattr(order, "payment"):
            raise serializers.ValidationError("이미 결제가 생성된 주문입니다.")

        return value


class PaymentConfirmSerializer(serializers.Serializer):
    # 요청 필드
    order_id = serializers.IntegerField(write_only=True)
    payment_key = serializers.CharField(write_only=True)

    # 응답 필드
    status = serializers.CharField(read_only=True)

    def validate(self, data):
        try:
            order = Order.objects.get(id=data["order_id"])
        except Order.DoesNotExist:
            raise serializers.ValidationError("존재하지 않는 주문입니다.")

        # Payment 확인
        try:
            payment = order.payment
        except Payment.DoesNotExist:
            raise serializers.ValidationError("결제 정보가 존재하지 않습니다.")

        # payment_key 검증
        if payment.payment_key != data["payment_key"]:
            raise serializers.ValidationError("유효하지 않은 payment_key입니다.")

        # 이미 결제 완료된 경우
        if payment.status == Payment.Status.PAID:
            raise serializers.ValidationError("이미 결제 완료된 주문입니다.")

        data["payment"] = payment
        data["order"] = order
        return data


class PaymentListSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id")
    order_status = serializers.CharField(source="order.status")

    class Meta:
        model = Payment
        fields = [
            "id",
            "order_id",
            "order_status",
            "payment_key",
            "price",
            "status",
            "created_at",
            "paid_at",
        ]
