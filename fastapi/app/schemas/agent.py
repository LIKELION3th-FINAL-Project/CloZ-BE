from pydantic import BaseModel
from typing import Optional


# ── Request 관련 ──

class UserInfo(BaseModel):
    user_id: int
    gender: str
    height: float
    weight: float
    styles: list[str]


class ClosetItem(BaseModel):
    image_url: str
    style_cat: str = ""
    id: str = ""
    embedding: Optional[list[float]] = None


class ClosetData(BaseModel):
    TOP: list[ClosetItem] = []
    BOTTOM: list[ClosetItem] = []
    OUTER: list[ClosetItem] = []


class AgentRequest(BaseModel):
    session_id: str = ""
    user: UserInfo
    closet: ClosetData
    message: str


# ── Response 관련 ──

class ProductInfo(BaseModel):
    product_id: int
    category_main: str
    category_sub: str
    product_name: str


class OutfitInfo(BaseModel):
    outfit_id: int
    image_url: str
    products: list[ProductInfo]


class AgentResponse(BaseModel):
    session_id: str = ""
    message: str
    outfits: list[OutfitInfo] = []
