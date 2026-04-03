import logging

from django.conf import settings
from botocore.exceptions import BotoCoreError, ClientError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cloz.image_bridge import image_key_to_presigned_url

logger = logging.getLogger(__name__)


def _presigned_ttl() -> int:
    raw = getattr(settings, "AWS_PRESIGNED_URL_EXPIRE_SECONDS", None)
    if raw is not None:
        return int(raw)
    return 3600


class PresignedImageView(APIView):
    # fastapi가 반환한 S3 image_key를 브라우저용 presigned get url로로 바꿔준다. <- 브라우저는 s3키가 아니라 get이 가능한 url필요 

    permission_classes = [IsAuthenticated]

    def get(self, request):
        image_key = (request.query_params.get("image_key") or "").strip()
        if not image_key:
            return Response(
                {"detail": "image_key query parameter is required."},
                status=400,
            )

        prefix = f"recommendations/{request.user.pk}/"
        if not image_key.startswith(prefix):
            return Response(
                {"detail": "You may only request URLs for your own recommendation images."},
                status=403,
            )

        try:
            url = image_key_to_presigned_url(image_key, expires_in=_presigned_ttl())
        except (BotoCoreError, ClientError, TypeError, ValueError) as exc:
            logger.exception("presigned url failed for key=%s", image_key)
            return Response(
                {"detail": f"Could not generate image URL: {exc}"},
                status=502,
            )

        return Response({"image_url": url, "image_key": image_key})

