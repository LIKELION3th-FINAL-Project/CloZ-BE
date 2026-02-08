from rest_framework import serializers
from .models import Closet


class ClosetListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="get_category_display")
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Closet
        fields = [
            "id",
            "category",
            "image_url",
            "created_at",
        ]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ClosetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Closet
        fields = [
            "category",
            "image",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return Closet.objects.create(user=user, **validated_data)
