import io
import boto3
from PIL import Image
from app.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


def download_image_from_s3(image_key: str) -> Image.Image:
    """
    S3 key (예: 'closet_images/abc123.jpg') → PIL Image 객체 반환
    """
    client = get_s3_client()
    response = client.get_object(
        Bucket=settings.AWS_S3_BUCKET_NAME,
        Key=image_key,
    )
    image_bytes = response["Body"].read()
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")