from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Cart(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="cart"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart(user={self.user})"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="items"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(
        "product.Product", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.product} x {self.quantity}"
