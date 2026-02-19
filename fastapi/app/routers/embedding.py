"""
/api/embeddings/ — Closet 이미지 임베딩 생성 엔드포인트

흐름:
  1) Django가 Closet 생성 후 이 엔드포인트를 호출
  2) image_url에서 이미지 다운로드 → 임시 파일 저장
  3) CLIPEncoder → 임베딩 벡터 + 스타일 분류
  4) DB에 embedding, style_cat 저장
  5) 결과 반환
"""
import tempfile

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.state import get_clip_encoder
from app.schemas.embedding import EmbeddingRequest, EmbeddingResponse
from app.image_utils import download_image_from_url
from app.style_classifier import classify_style

router = APIRouter(tags=["embedding"])


@router.post("/embeddings/", response_model=EmbeddingResponse)
async def create_embedding(
    req: EmbeddingRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Closet 아이템의 이미지를 Fashion CLIP으로 임베딩하고
    스타일 카테고리를 분류하여 DB에 저장합니다.
    """
    encoder = get_clip_encoder()

    # ── 1. 이미지 다운로드 ──
    try:
        image = await download_image_from_url(req.image_url)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"이미지 다운로드 실패: {str(e)}",
        )

    # ── 2. 임시 파일에 저장 (CLIPEncoder는 파일 경로를 받음) ──
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
        image.save(tmp, format="JPEG")
        tmp.flush()

        # ── 3. Fashion CLIP 추론 ──
        # 임베딩 벡터 (512차원, torch.Tensor → list)
        embedding_tensor = encoder.encode_image(tmp.name)
        embedding_list = embedding_tensor.cpu().tolist()

        # 스타일 분류 (zero-shot)
        style_cat = classify_style(encoder, tmp.name)

    # ── 4. DB에 embedding + style_cat 저장 ──
    await session.execute(
        text("""
            UPDATE closet_closet
            SET embedding  = :embedding,
                style_cat  = :style_cat
            WHERE id = :id
        """),
        {
            "embedding": str(embedding_list),
            "style_cat": style_cat,
            "id": req.id,
        },
    )
    await session.commit()

    # ── 5. 응답 반환 ──
    return EmbeddingResponse(
        id=req.id,
        category=req.category,
        image_url=req.image_url,
        created_at=req.created_at,
        style_cat=style_cat,
        embedding=embedding_list,
    )
