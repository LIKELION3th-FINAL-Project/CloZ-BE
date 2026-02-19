"""
Celery 비동기 태스크
- 임베딩 생성: 이미지 다운로드 → CLIPEncoder 추론 → DB 저장
- Django에서 Closet 생성 후 이 태스크를 호출하면 백그라운드에서 처리
"""
import sys
import tempfile

import httpx
from PIL import Image
import io

from app.worker import celery_app
from app.config import settings

# 서브모듈 경로 추가
sys.path.insert(0, f"{settings.MODELS_ROOT}/src")


def _to_internal_url(image_url: str) -> str:
    """localhost → Docker 내부 서비스명 치환"""
    return (
        image_url
        .replace("http://localhost:8000", "http://app:8000")
        .replace("http://localhost", "http://nginx")
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def generate_embedding(self, closet_id: int, image_url: str):
    """
    백그라운드에서 Closet 이미지 임베딩 + 스타일 분류 → DB 저장.

    Args:
        closet_id: Closet 레코드 ID
        image_url: 이미지 URL (Django가 제공)
    """
    try:
        # ── 1. 이미지 다운로드 ──
        internal_url = _to_internal_url(image_url)
        response = httpx.get(internal_url, timeout=30.0)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")

        # ── 2. CLIPEncoder 로드 & 추론 ──
        from fashion_engine.encoder import CLIPEncoder
        from app.style_classifier import classify_style

        encoder = CLIPEncoder()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            image.save(tmp, format="JPEG")
            tmp.flush()

            # 임베딩 벡터
            embedding_tensor = encoder.encode_image(tmp.name)
            embedding_list = embedding_tensor.cpu().tolist()

            # 스타일 분류
            style_cat = classify_style(encoder, tmp.name)

        # ── 3. DB 저장 (동기 방식 — Celery 워커는 동기) ──
        import psycopg2
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            dbname=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE closet_closet
                    SET embedding = %s, style_cat = %s
                    WHERE id = %s
                    """,
                    (str(embedding_list), style_cat, closet_id),
                )
            conn.commit()
        finally:
            conn.close()

        return {
            "closet_id": closet_id,
            "style_cat": style_cat,
            "embedding_dim": len(embedding_list),
        }

    except Exception as exc:
        raise self.retry(exc=exc)
