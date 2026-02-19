from django.db import models
from django.conf import settings
from pgvector.django import VectorField

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

    style_cat = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="스타일 카테고리",
    )

    class EmbeddingStatus(models.TextChoices):
        PENDING = "PENDING", "대기"
        PROCESSING = "PROCESSING", "처리중"
        DONE = "DONE", "완료"
        FAILED = "FAILED", "실패"

    embedding_status = models.CharField(
        max_length=20,
        choices=EmbeddingStatus.choices,
        default=EmbeddingStatus.PENDING,
    )

    # 임베딩 벡터 필드 추가 
    embedding = VectorField(
        dimensions=512,       # 사용하는 모델 출력 차원에 맞춰 조정
        null=True,
        blank=True,
    )


    def __str__(self):
        return f"{self.category} - {self.image}"
