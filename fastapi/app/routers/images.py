import io

from fastapi import APIRouter, HTTPException, Query
from PIL import Image

from app.s3 import (
    generate_presigned_image_url,
    upload_generated_file,
    upload_generated_image,
)
from app.schemas.image import (
    GeneratedImageUploadRequest,
    ImageKeyResponse,
    PresignedUrlResponse,
)

router = APIRouter(tags=["images"])


@router.post("/images/upload", response_model=ImageKeyResponse)
async def upload_generated_output(req: GeneratedImageUploadRequest):
    try:
        image_bytes = req.generated.decode_bytes()
        if image_bytes is not None:
            image_key = upload_generated_image(
                image_bytes=image_bytes,
                user_id=req.user_id,
                session_id=req.session_id,
            )
        else:
            image_key = upload_generated_file(
                local_path=req.generated.local_output_path or "",
                user_id=req.user_id,
                session_id=req.session_id,
            )
        return ImageKeyResponse(image_key=image_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"generated image upload failed: {exc}")


@router.post("/images/upload-test", response_model=ImageKeyResponse)
async def upload_generated_output_test(
    user_id: int = Query(...),
    session_id: str = Query(...),
):
    try:
        buffer = io.BytesIO()
        Image.new("RGB", (2, 2), color=(255, 0, 0)).save(buffer, format="PNG")
        image_key = upload_generated_image(
            image_bytes=buffer.getvalue(),
            user_id=user_id,
            session_id=session_id,
        )
        return ImageKeyResponse(image_key=image_key)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"upload test failed: {exc}")


@router.get("/images/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    image_key: str = Query(...),
    expires_in: int = Query(default=0),
):
    try:
        image_url = generate_presigned_image_url(
            image_key=image_key,
            expires_in=expires_in if expires_in > 0 else None,
        )
        return PresignedUrlResponse(image_url=image_url)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"presigned url generation failed: {exc}")
