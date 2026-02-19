from django.db import models
from pgvector.django import VectorField

class Product(models.Model):
    """
    서비스에서 사용하는 상품 도메인 모델
    """
    # 카테고리
    category_main = models.CharField(
        max_length=30,
        db_index=True
    )
    category_sub = models.CharField(
        max_length=30,
        db_index=True
    )

    # 기본 정보
    brand = models.CharField(
        max_length=100,
        db_index=True
    )
    product_name = models.CharField(
        max_length=100
    )

    # 가격
    price = models.PositiveIntegerField(
        help_text="상품 가격 (원 단위)"
    )

    # 외부 링크
    product_url = models.URLField(
        max_length=500
    )

    # 이미지 경로 (S3/외부 CDN/정적 URL)
    product_image_path = models.URLField(
        max_length=500
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category_main", "category_sub"]),
        ]

    def __str__(self):
        return f"[{self.brand}] {self.product_name}"


class ReferenceEmbedding(models.Model):
    # CSV의 id: 예) "리조트/f47276e9.jpg"
    source_id = models.CharField(max_length=255, unique=True, db_index=True)
    style_cat = models.CharField(max_length=50, db_index=True)
    embedding = VectorField(dimensions=512)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reference_embeddings"