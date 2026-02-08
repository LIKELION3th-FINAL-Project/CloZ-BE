from django.urls import path
from .views import PaymentPrepareView, PaymentConfirmView, PaymentListView

urlpatterns = [
    path(
        "prepare/",
        PaymentPrepareView.as_view(),
        name="payment-prepare",  # 결제 요청 생성
    ),
    path(
        "confirm/",
        PaymentConfirmView.as_view(),
        name="payment-confirm",  # 결제 성공 콜백
    ),
    path(
        "",
        PaymentListView.as_view(),
        name="payment-list",  # 결제 내역 조회
    ),
]
