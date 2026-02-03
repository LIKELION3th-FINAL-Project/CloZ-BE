from django.db import models
from django.conf import settings

class Closet(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="closets"
    )

    class Category(models.TextChoices):
        TOP = "TOP", "상의"
        BOTTOM = "BOTTOM", "하의"
        OUTER = "OUTER", "아우터"

    category = models.CharField(
        max_length=10,
        choices=Category.choices
    )

    image_url = models.URLField(
        max_length=500
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.category} - {self.image_url}"
