from django.urls import path
from .views import (
    SignupView,
    LoginView,
    SocialAuthView,
    MyPageView,
    AddressCreateView,
    AddressUpdateView,
)

urlpatterns = [
    path("signup/", SignupView.as_view()),
    path("login/", LoginView.as_view()),
    path("social-auth/", SocialAuthView.as_view()),
    path("mypage/", MyPageView.as_view()),
    path("addresses/", AddressCreateView.as_view()),
    path("addresses/<int:address_id>/", AddressUpdateView.as_view()),
]
