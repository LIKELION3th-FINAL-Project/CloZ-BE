from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Address
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    SignupSerializer,
    LoginSerializer,
    MyPageSerializer,
    AddressCreateSerializer,
    AddressUpdateSerializer,
)

User = get_user_model()


def issue_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        if User.objects.filter(
            login_id=request.data.get("login_id")
        ).exists():
            return Response(
                {"message": "이미 존재하는 사용자입니다."},
                status=status.HTTP_409_CONFLICT
            )

        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        access_token = issue_token(user)

        return Response(
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "access_token": access_token,
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        access_token = issue_token(user)

        return Response(
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "access_token": access_token,
            },
            status=status.HTTP_200_OK
        )


class SocialSignupView(APIView):
    permission_classes = []

    def post(self, request):
        provider = request.data.get("provider")
        provider_token = request.data.get("provider_token")

        # TODO: provider_token 검증 (카카오/네이버 API)
        social_id = f"{provider}_{provider_token}"

        user, created = User.objects.get_or_create(
            login_id=f"{social_id}@social.user",
            defaults={
                "nickname": request.data.get("nickname"),
                "height": request.data.get("height"),
                "weight": request.data.get("weight"),
                "gender": request.data.get("gender"),
                "profile_image": request.data.get(
                    "profile_image", ""
                ),
            }
        )

        access_token = issue_token(user)

        return Response(
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "access_token": access_token,
            },
            status=status.HTTP_200_OK
        )


class MyPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MyPageSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddressCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddressCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        address = serializer.save()

        return Response(
            {
                "address_id": address.id,
                "message": "created"
            },
            status=status.HTTP_201_CREATED
        )


class AddressUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, address_id):
        try:
            address = Address.objects.get(
                id=address_id,
                user=request.user
            )
        except Address.DoesNotExist:
            return Response(
                {"message": "not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = AddressUpdateSerializer(
            address,
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "updated"},
            status=status.HTTP_200_OK
        )
