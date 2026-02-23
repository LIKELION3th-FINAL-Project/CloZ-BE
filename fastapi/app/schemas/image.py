import base64
from typing import Optional

from pydantic import BaseModel, model_validator


class GeneratedImageInput(BaseModel):
    image_bytes_base64: Optional[str] = None
    local_output_path: Optional[str] = None

    @model_validator(mode="after")
    def validate_exclusive_input(self):
        has_bytes = bool(self.image_bytes_base64)
        has_path = bool(self.local_output_path)
        if has_bytes == has_path:
            raise ValueError("Provide exactly one of image_bytes_base64 or local_output_path")
        return self

    def decode_bytes(self) -> Optional[bytes]:
        if not self.image_bytes_base64:
            return None
        return base64.b64decode(self.image_bytes_base64)


class GeneratedImageUploadRequest(BaseModel):
    user_id: int
    session_id: str
    generated: GeneratedImageInput


class ImageKeyResponse(BaseModel):
    image_key: str


class PresignedUrlResponse(BaseModel):
    image_url: str
