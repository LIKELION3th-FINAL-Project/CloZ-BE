from rest_framework import serializers
from .models import Closet

class ClosetListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="get_category_display")

    class Meta:
        model = Closet
        fields = [
            "id",
            "category",
            "image_url",
            "created_at",
        ]
class ClosetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Closet
        fields = [
            "category",
            "image_url",
        ]

    def create(self, validated_data):
        user = self.context["request"].user
        return Closet.objects.create(user=user, **validated_data)
