from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PAID = "PAID"
        CANCELED = "CANCELED"
        FAILED = "FAILED"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def total_quantity(self):
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, related_name="items", on_delete=models.CASCADE
    )
    product = models.ForeignKey("product.Product", on_delete=models.PROTECT)
    price = models.IntegerField()      # 주문 당시 단가
    quantity = models.IntegerField()
