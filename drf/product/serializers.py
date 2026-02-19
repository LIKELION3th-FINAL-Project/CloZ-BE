from rest_framework import serializers
from .models import Product


# 상품 전체 목록 조회, 카테고리기반 목록 조회, 상품 검색
class ProductListSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source="product_image_path")

    class Meta:
        model = Product
        fields = [
            "id",
            "category_main",
            "category_sub",
            "brand",
            "product_name",
            "price",
            "product_url",
            "image_url",
        ]


# 상품 상세 조회
class ProductDetailSerializer(serializers.ModelSerializer):
    image_url = serializers.CharField(source="product_image_path")

    class Meta:
        model = Product
        fields = [
            "id",
            "category_main",
            "category_sub",
            "brand",
            "product_name",
            "price",
            "product_url",
            "image_url",
        ]
