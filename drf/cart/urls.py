from django.urls import path
from .views import CartView, CartItemView

urlpatterns = [
    path("", CartView.as_view()),
    path("items/", CartItemView.as_view()),
    path("items/<int:product_id>/", CartItemView.as_view()),
]
