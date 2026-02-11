from fastapi import APIRouter

router = APIRouter(tags=["embedding"])


@router.post("/embeddings/")
async def create_embedding():
    """임베딩 생성 엔드포인트 (TODO: 구현)"""
    return {"message": "embedding endpoint"}
