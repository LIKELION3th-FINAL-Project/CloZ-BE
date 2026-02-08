from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Closet
from .serializers import ClosetListSerializer, ClosetCreateSerializer


class ClosetListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Closet.objects.filter(
            user=request.user
        ).order_by("-created_at")
        serializer = ClosetListSerializer(
            qs, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClosetCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ClosetCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(
            {"message": "added"},
            status=status.HTTP_201_CREATED
        )


class ClosetDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, closet_id):
        try:
            closet = Closet.objects.get(
                id=closet_id,
                user=request.user
            )
        except Closet.DoesNotExist:
            return Response(
                {"message": "not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # 이미지 파일도 삭제
        if closet.image:
            closet.image.delete(save=False)

        closet.delete()
        return Response(
            {"message": "deleted"},
            status=status.HTTP_200_OK
        )
