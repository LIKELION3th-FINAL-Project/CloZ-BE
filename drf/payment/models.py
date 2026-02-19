from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"     # 결제 대기
        PAID = "PAID"           # 결제 완료
        FAILED = "FAILED"       # 결제 실패
        CANCELED = "CANCELED"   # 결제 취소

    order = models.OneToOneField(
        "order.Order",
        on_delete=models.CASCADE,
        related_name="payment"
    )
    payment_key = models.CharField(
        max_length=200, unique=True, null=True, blank=True
    )
    price = models.IntegerField()  # 결제 금액
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"Payment {self.id} - "
            f"Order {self.order_id} - {self.status}"
        )
