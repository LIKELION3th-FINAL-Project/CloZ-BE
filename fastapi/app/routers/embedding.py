from app.s3 import download_image_from_s3

@router.post("/embeddings/")
async def create_embedding(
    closet_id: int,
    session: AsyncSession = Depends(get_session),
):
    fclip = get_fclip()

    # 1) DB에서 이미지 S3 key 조회
    result = await session.execute(
        text("SELECT image FROM closet_closet WHERE id = :id"),
        {"id": closet_id},
    )
    row = result.fetchone()
    if not row:
        return {"error": "closet not found"}

    # 2) S3에서 이미지 다운로드 → 임베딩 생성
    image = download_image_from_s3(row[0])         # ← 변경된 부분
    embedding = fclip.encode_images([image], batch_size=1)[0]

    # 3) DB에 임베딩 저장
    await session.execute(
        text("UPDATE closet_closet SET embedding = :emb WHERE id = :id"),
        {"emb": embedding.tolist(), "id": closet_id},
    )
    await session.commit()

    return {"closet_id": closet_id, "embedding_dim": len(embedding)}