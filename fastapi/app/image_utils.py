"""
이미지 URL → PIL Image 다운로드 유틸리티
- Django/nginx가 서빙하는 image_url을 받아 PIL Image로 변환
- Docker 내부 네트워크에서는 서비스명(app, nginx)으로 접근
"""
import io

import httpx
from PIL import Image


def _to_internal_url(image_url: str) -> str:
    """
    외부 URL(localhost)을 Docker 내부 서비스명으로 치환.
    FastAPI 컨테이너에서 localhost는 자기 자신이므로
    Django(app:8000) 또는 nginx로 바꿔야 이미지에 접근 가능.
    """
    return (
        image_url
        .replace("http://localhost:8000", "http://app:8000")
        .replace("http://localhost", "http://nginx")
    )


async def download_image_from_url(image_url: str) -> Image.Image:
    """HTTP URL에서 이미지를 다운로드하여 PIL Image로 반환."""
    internal_url = _to_internal_url(image_url)

    async with httpx.AsyncClient() as client:
        response = await client.get(internal_url, timeout=30.0)
        response.raise_for_status()

    return Image.open(io.BytesIO(response.content)).convert("RGB")
