from pydantic import BaseModel
from datetime import datetime


class EmbeddingRequest(BaseModel):
    id: int
    category: str
    image_url: str
    created_at: datetime


class EmbeddingResponse(BaseModel):
    id: int
    category: str
    image_url: str
    created_at: datetime
    style_cat: str
    embedding: list[float]
