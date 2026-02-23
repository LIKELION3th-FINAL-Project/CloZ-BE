import boto3
from django.conf import settings


def image_key_to_presigned_url(image_key: str, expires_in: int = 3600) -> str:
    """
    FastAPI가 반환한 image_key를 프론트 전달용 presigned URL로 변환한다.
    운영 환경에서는 IAM Role(기본 credential chain) 사용을 권장한다.
    """
    client = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
    )
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": image_key,
        },
        ExpiresIn=expires_in,
    )
