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

    image = models.ImageField(
        upload_to="closet_images/",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.category} - {self.image}"
