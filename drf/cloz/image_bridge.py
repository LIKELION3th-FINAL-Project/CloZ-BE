import boto3
from django.conf import settings
from botocore.client import Config


def image_key_to_presigned_url(image_key: str, expires_in: int = 3600) -> str:
    # FastAPI가 반환한 image_key를 프론트 전달용 presigned URL로 변환한다.
    client = boto3.client(
        "s3",
        region_name=settings.AWS_S3_REGION_NAME,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=Config(
            signature_version="s3v4",            
            s3={"addressing_style": "path"}        
        )
    )
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.AWS_S3_BUCKET_NAME,
            "Key": image_key,
        },
        ExpiresIn=expires_in,
    )
