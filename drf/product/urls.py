from django.urls import path
from . import views

urlpatterns = []

# api/products
urlpatterns = [
    path(
        "",
        views.ProductListView.as_view(),
        name="product-list",  # 상품 전체 목록 조회 get
    ),
    path(
        "categories/<str:category>/",
        views.ProductByCategoryView.as_view(),
        name="product-by-category",  # 카테고리기반 목록 조회 get
    ),
    path(
        "search/",
        views.ProductSearchView.as_view(),
        name="product-search",  # 상품 검색 get
    ),
    path(
        "<int:product_id>/",
        views.ProductDetailView.as_view(),
        name="product-detail",  # 상품 상세 조회 get
    ),
]
