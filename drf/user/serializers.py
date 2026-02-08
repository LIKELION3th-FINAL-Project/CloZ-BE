from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Style, UserStyle, Address

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    styles = serializers.ListField(
        child=serializers.CharField(),
        write_only=True
    )

    class Meta:
        model = User
        fields = [
            "login_id",
            "password",
            "nickname",
            "height",
            "weight",
            "gender",
            "profile_image",
            "styles",
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

    def validate_styles(self, value):
        if not (1 <= len(value) <= 3):
            raise serializers.ValidationError(
                "styles는 1~3개 선택해야 합니다."
            )
        return value

    def create(self, validated_data):
        styles = validated_data.pop("styles")

        user = User.objects.create_user(
            login_id=validated_data["login_id"],
            password=validated_data["password"],
            nickname=validated_data["nickname"],
            height=validated_data["height"],
            weight=validated_data["weight"],
            gender=validated_data["gender"],
            profile_image=validated_data.get("profile_image", ""),
        )

        style_objs = Style.objects.filter(name__in=styles)
        UserStyle.objects.bulk_create(
            [UserStyle(user=user, style=s) for s in style_objs]
        )

        return user


class LoginSerializer(serializers.Serializer):
    login_id = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            login_id=data["login_id"],
            password=data["password"]
        )
        if not user:
            raise serializers.ValidationError(
                "이메일 또는 비밀번호가 올바르지 않습니다."
            )
        data["user"] = user
        return data


class MyPageSerializer(serializers.ModelSerializer):
    styles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "nickname",
            "profile_image",
            "height",
            "weight",
            "gender",
            "styles",
        ]

    def get_styles(self, obj):
        return list(
            obj.user_styles.select_related("style")
            .values_list("style__name", flat=True)
        )


class AddressCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "receiver",
            "phone",
            "address",
            "is_default",
        ]

    def create(self, validated_data):
        user = self.context["request"].user

        # 기본 배송지 처리
        if validated_data.get("is_default", False):
            Address.objects.filter(
                user=user,
                is_default=True
            ).update(is_default=False)

        return Address.objects.create(
            user=user,
            **validated_data
        )


class AddressUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "receiver",
            "phone",
            "address",
            "is_default",
        ]

    def update(self, instance, validated_data):
        user = self.context["request"].user

        # 기본 배송지 변경 시 기존 기본 해제
        if validated_data.get("is_default", False):
            Address.objects.filter(
                user=user,
                is_default=True
            ).exclude(id=instance.id).update(is_default=False)

        return super().update(instance, validated_data)
