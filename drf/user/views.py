import requests
from django.conf import settings as django_settings
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
    MyPageUpdateSerializer,
    SocialSignupSerializer,
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


def exchange_code_for_token(provider, code, redirect_uri):
    """인가코드를 access_token으로 교환"""
    import logging
    logger = logging.getLogger(__name__)

    if provider == "kakao":
        resp = requests.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": django_settings.KAKAO_REST_API_KEY,
                "client_secret": django_settings.KAKAO_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=5,
        )
        data = resp.json()
        if "access_token" not in data:
            logger.warning(f"Kakao token exchange failed: {data}")
        return data.get("access_token")

    elif provider == "naver":
        resp = requests.post(
            "https://nid.naver.com/oauth2.0/token",
            data={
                "grant_type": "authorization_code",
                "client_id": django_settings.NAVER_CLIENT_ID,
                "client_secret": django_settings.NAVER_CLIENT_SECRET,
                "code": code,
                "state": "cloz_state",
            },
            timeout=5,
        )
        data = resp.json()
        if "access_token" not in data:
            logger.warning(f"Naver token exchange failed: {data}")
        return data.get("access_token")

    elif provider == "google":
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "grant_type": "authorization_code",
                "client_id": django_settings.GOOGLE_CLIENT_ID,
                "client_secret": django_settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
            timeout=5,
        )
        data = resp.json()
        if "access_token" not in data:
            logger.warning(f"Google token exchange failed: {data}")
        return data.get("access_token")

    return None


def verify_social_token(provider, access_token):
    """소셜 토큰을 검증하고 사용자 정보를 반환"""
    if provider == "kakao":
        resp = requests.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        kakao_account = data.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        return {
            "social_id": f"kakao_{data['id']}",
            "email": kakao_account.get("email", ""),
            "nickname": profile.get("nickname", ""),
        }

    elif provider == "naver":
        resp = requests.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        data = resp.json().get("response", {})
        return {
            "social_id": f"naver_{data.get('id')}",
            "email": data.get("email", ""),
            "nickname": data.get("nickname", ""),
        }

    elif provider == "google":
        resp = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=5,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return {
            "social_id": f"google_{data['id']}",
            "email": data.get("email", ""),
            "nickname": data.get("name", ""),
        }

    return None


def resolve_social_access_token(request_data):
    """요청 데이터에서 소셜 access_token을 확보한다.
    직접 전달된 access_token을 사용하거나, code로 교환한다.
    반환: (social_info, social_access_token, error_response)
    """
    provider = request_data.get("provider")
    access_token = request_data.get("access_token")
    code = request_data.get("code")
    redirect_uri = request_data.get("redirect_uri")

    if provider not in ("kakao", "naver", "google"):
        return None, None, Response(
            {"message": "지원하지 않는 provider입니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # code가 있으면 access_token으로 교환
    if code and redirect_uri:
        if redirect_uri not in django_settings.SOCIAL_LOGIN_REDIRECT_URIS:
            return None, None, Response(
                {"message": "허용되지 않은 redirect_uri입니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        access_token = exchange_code_for_token(
            provider, code, redirect_uri
        )
        if not access_token:
            return None, None, Response(
                {"message": f"{provider} 인가코드로 토큰 교환에 실패했습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if not access_token:
        return None, None, Response(
            {"message": "access_token 또는 code가 필요합니다."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    social_info = verify_social_token(provider, access_token)
    if not social_info:
        return None, None, Response(
            {"message": "소셜 토큰 검증에 실패했습니다."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    return social_info, access_token, None


class SocialAuthView(APIView):
    """소셜 인증 (로그인 + 회원가입 통합)"""
    permission_classes = []

    def post(self, request):
        social_info, social_access_token, error_response = (
            resolve_social_access_token(request.data)
        )
        if error_response:
            return error_response

        social_id = social_info["social_id"]
        login_id = (
            social_info.get("email")
            or f"{social_id}@social.user"
        )

        # 1) 기존 유저 → 로그인
        user = User.objects.filter(login_id=login_id).first()
        if user:
            jwt_token = issue_token(user)
            return Response(
                {
                    "user_id": user.id,
                    "nickname": user.nickname,
                    "access_token": jwt_token,
                    "is_new_user": False,
                },
                status=status.HTTP_200_OK,
            )

        # 2) 신규 유저 + 프로필 필드 없음 → 소셜 정보만 반환
        has_profile = all(
            key in request.data
            for key in ("nickname", "height", "weight", "gender", "styles")
        )
        if not has_profile:
            return Response(
                {
                    "is_new_user": True,
                    "email": social_info.get("email", ""),
                    "nickname": social_info.get("nickname", ""),
                    "social_access_token": social_access_token,
                },
                status=status.HTTP_200_OK,
            )

        # 3) 신규 유저 + 프로필 필드 있음 → 회원가입
        serializer = SocialSignupSerializer(
            data=request.data,
            context={"login_id": login_id},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        jwt_token = issue_token(user)

        return Response(
            {
                "user_id": user.id,
                "nickname": user.nickname,
                "access_token": jwt_token,
                "is_new_user": True,
            },
            status=status.HTTP_201_CREATED,
        )


class MyPageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MyPageSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = MyPageUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            MyPageSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


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
