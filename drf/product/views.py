from django.shortcuts import render
from rest_framework.views import APIView
from .models import Product
from .serializers import (ProductListSerializer,ProductDetailSerializer)
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

# 상품 전체 목록 조회 (무한 스크롤)
class ProductListView(APIView): 
    def get(self, request):
        offset = int (request.query_params.get("offset",0))
        limit = int(request.query_params.get("limit", 20))

        qs= Product.objects.all().order_by("-created_at")[offset:offset+limit]
        serializer = ProductListSerializer(qs, many=True)

        return Response({
            "offset": offset,
            "limit": limit,
            "count": qs.count(),
            "products": serializer.data,    
        })
    
# 카테고리기반 목록 조회 
class ProductByCategoryView(APIView):
    def get(self, request, category):
        offset = int(request.query_params.get("offset", 0))
        limit = int(request.query_params.get("limit", 20))
        category_sub = request.query_params.get("category_sub", None)

        qs = Product.objects.filter(category_main=category).order_by("-created_at")

        if category_sub:
            qs = qs.filter(category_sub__iexact=category_sub)

        sliced = qs[offset: offset + limit]
        serializer = ProductListSerializer(sliced, many=True)

        return Response({
            "offset": offset,
            "limit": limit,
            "products": serializer.data,
        })

# 상품 검색 (PostgreSQL Full-Text)
class ProductSearchView(APIView):
    def get(self, request):
        keyword = request.query_params.get("keyword")
        if not keyword:
            return Response({"products": []})

        offset = int(request.query_params.get("offset", 0))
        limit = int(request.query_params.get("limit", 20))

        vector = (
            SearchVector("product_name", weight="A") +
            SearchVector("brand", weight="B") +
            SearchVector("category_main", weight="C") +
            SearchVector("category_sub", weight="C")
        )
        query = SearchQuery(keyword)

        qs = (
            Product.objects
            .annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.1)
            .order_by("-rank")
        )

        sliced = qs[offset: offset + limit]
        serializer = ProductListSerializer(sliced, many=True)

        return Response({
            "keyword": keyword,
            "offset": offset,
            "limit": limit,
            "products": serializer.data,
        })


# 상품 상세 조회 
class ProductDetailView(APIView):
    def get(self, request, product_id):
        product = Product.objects.get(id=product_id)
        serializer = ProductDetailSerializer(product)

        return Response(serializer.data)
