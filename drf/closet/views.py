import logging
import threading
import requests as http_requests

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.db import close_old_connections

from .models import Closet
from .serializers import ClosetListSerializer, ClosetCreateSerializer

logger = logging.getLogger(__name__)

# Docker 내부에서 FastAPI(ai) 서비스 접근 URL
FASTAPI_EMBEDDING_URL = "http://ai:8001/api/embeddings/"


def trigger_embedding_async(closet, request):
    """Upload 응답과 분리해 임베딩 처리를 백그라운드로 실행한다."""
    if not closet.image:
        Closet.objects.filter(id=closet.id).update(
            embedding_status=Closet.EmbeddingStatus.FAILED
        )
        logger.warning(
            "[closet] 이미지가 없어 임베딩을 건너뜁니다: closet_id=%s",
            closet.id,
        )
        return

    try:
        image_url = request.build_absolute_uri(closet.image.url)
    except Exception:
        Closet.objects.filter(id=closet.id).update(
            embedding_status=Closet.EmbeddingStatus.FAILED
        )
        logger.exception(
            "[closet] image_url 생성 실패: closet_id=%s",
            closet.id,
        )
        return

    payload = {
        "id": closet.id,
        "category": closet.get_category_display(),
        "image_url": image_url,
        "created_at": closet.created_at.isoformat(),
    }

    def _worker():
        close_old_connections()
        try:
            Closet.objects.filter(id=closet.id).update(
                embedding_status=Closet.EmbeddingStatus.PROCESSING
            )
            resp = http_requests.post(
                FASTAPI_EMBEDDING_URL,
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            logger.info(
                "[closet] 임베딩 요청 완료: closet_id=%s",
                closet.id,
            )
        except Exception:
            Closet.objects.filter(id=closet.id).update(
                embedding_status=Closet.EmbeddingStatus.FAILED
            )
            logger.exception(
                "[closet] 임베딩 요청 실패: closet_id=%s",
                closet.id,
            )
        finally:
            close_old_connections()

    threading.Thread(target=_worker, daemon=True).start()


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
        try:
            closet = serializer.save()
        except Exception:
            logger.exception(
                "[closet] 업로드 실패(스토리지/권한 오류 가능): user_id=%s",
                request.user.id,
            )
            return Response(
                {"message": "image upload failed"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        trigger_embedding_async(closet, request)

        return Response(
            {
                "message": "added",
                "closet_id": closet.id,
                "embedding_status": closet.embedding_status,
            },
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

        # 이미지 파일 삭제 실패가 있어도 DB 레코드 삭제는 진행한다.
        if closet.image:
            try:
                closet.image.delete(save=False)
            except Exception:
                logger.exception(
                    "[closet] 이미지 파일 삭제 실패(권한 오류 가능): closet_id=%s",
                    closet.id,
                )

        closet.delete()
        return Response(
            {"message": "deleted"},
            status=status.HTTP_200_OK
        )
