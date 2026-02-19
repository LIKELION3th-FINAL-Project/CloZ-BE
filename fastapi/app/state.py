import sys
import types
from app.config import settings

# ── 서브모듈 패키지 등록 (__init__.py 실행 우회) ──
_gp_root = f"{settings.MODELS_ROOT}/src/generation_pipeline"

# generation_pipeline (부모 패키지)
gp = types.ModuleType("generation_pipeline")
gp.__path__ = [_gp_root]
gp.__package__ = "generation_pipeline"
sys.modules["generation_pipeline"] = gp

# generation_pipeline.fashion_engine (서브 패키지)
fe = types.ModuleType("generation_pipeline.fashion_engine")
fe.__path__ = [f"{_gp_root}/fashion_engine"]
fe.__package__ = "generation_pipeline.fashion_engine"
sys.modules["generation_pipeline.fashion_engine"] = fe

# generation_pipeline.utils (서브 패키지)
ut = types.ModuleType("generation_pipeline.utils")
ut.__path__ = [f"{_gp_root}/utils"]
ut.__package__ = "generation_pipeline.utils"
sys.modules["generation_pipeline.utils"] = ut

# 전역 상태
clip_encoder = None    # Fashion CLIP (이미지 임베딩)
understand_model = None  # LLM (유저 의도 분석)


def load_all():
    global clip_encoder, understand_model

    # 1) Fashion CLIP — 이미지 임베딩 + 스타일 분류
    from generation_pipeline.fashion_engine.encoder import CLIPEncoder

    print("[startup] Fashion CLIP 로딩 중...")
    clip_encoder = CLIPEncoder()
    print("[startup] Fashion CLIP 로드 완료")

    # 2) LLM — Upstage Solar Pro3 API 클라이언트
    from generation_pipeline.understand_model.understand_model import UnderstandModel
    print("[startup] UnderstandModel(LLM) 초기화 중...")
    understand_model = UnderstandModel()
    print("[startup] UnderstandModel 초기화 완료")


def get_clip_encoder():
    """로드된 CLIPEncoder 인스턴스를 반환합니다."""
    if clip_encoder is None:
        raise RuntimeError("CLIPEncoder가 아직 로드되지 않았습니다.")
    return clip_encoder


def get_understand_model():
    """로드된 UnderstandModel 인스턴스를 반환합니다."""
    if understand_model is None:
        raise RuntimeError("UnderstandModel이 아직 로드되지 않았습니다.")
    return understand_model
