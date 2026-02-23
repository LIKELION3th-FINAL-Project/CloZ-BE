import io
import mimetypes
import uuid
from pathlib import Path
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from PIL import Image

from app.config import settings


def _resolve_local_output_path(local_path: str) -> Path:
    raw = Path(local_path)
    candidates = [raw]
    if not raw.is_absolute():
        candidates.extend([
            Path(settings.MODELS_ROOT) / raw,
            Path(settings.MODELS_ROOT) / "src" / raw,
        ])

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    raise FileNotFoundError(f"generated output file not found: {local_path}")


def get_s3_client():
    kwargs = {"region_name": settings.AWS_S3_REGION_NAME}
    auth_mode = settings.AWS_AUTH_MODE.lower()

    if auth_mode == "static":
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    elif auth_mode == "auto":
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    elif auth_mode != "iam_role":
        raise ValueError(
            "AWS_AUTH_MODE must be one of: auto, static, iam_role"
        )

    return boto3.client("s3", **kwargs)


def build_recommendation_image_key(user_id: int, session_id: str, extension: str = ".png") -> str:
    safe_ext = extension if extension.startswith(".") else f".{extension}"
    return f"recommendations/{user_id}/{session_id}/{uuid.uuid4().hex}{safe_ext}"


def upload_generated_image(image_bytes: bytes, user_id: int, session_id: str) -> str:
    if not image_bytes:
        raise ValueError("image_bytes must not be empty")

    image_key = build_recommendation_image_key(user_id=user_id, session_id=session_id, extension=".png")
    client = get_s3_client()
    client.put_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=image_key,
        Body=image_bytes,
        ContentType="image/png",
    )
    return image_key


def upload_generated_file(local_path: str, user_id: int, session_id: str) -> str:
    path = _resolve_local_output_path(local_path)

    ext = path.suffix or ".png"
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    image_key = build_recommendation_image_key(user_id=user_id, session_id=session_id, extension=ext)
    client = get_s3_client()
    client.upload_file(
        Filename=str(path),
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=image_key,
        ExtraArgs={"ContentType": content_type},
    )
    return image_key


def upload_generated_output(
    *,
    user_id: int,
    session_id: str,
    image_bytes: Optional[bytes] = None,
    local_output_path: Optional[str] = None,
) -> str:
    if image_bytes is not None and local_output_path is not None:
        raise ValueError("Provide either image_bytes or local_output_path, not both")
    if image_bytes is None and local_output_path is None:
        raise ValueError("Either image_bytes or local_output_path is required")

    if image_bytes is not None:
        return upload_generated_image(image_bytes=image_bytes, user_id=user_id, session_id=session_id)
    return upload_generated_file(local_path=local_output_path, user_id=user_id, session_id=session_id)


def generate_presigned_image_url(image_key: str, expires_in: Optional[int] = None) -> str:
    client = get_s3_client()
    ttl = expires_in or settings.AWS_PRESIGNED_URL_EXPIRE_SECONDS
    try:
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": image_key},
            ExpiresIn=ttl,
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"failed to generate presigned url: {exc}") from exc


def download_image_from_s3(image_key: str) -> Image.Image:
    client = get_s3_client()
    response = client.get_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=image_key,
    )
    image_bytes = response["Body"].read()
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")