"""
애플리케이션 전역 상태 관리
- 서버 시작 시 모델·프로세서를 한 번만 로드합니다.
"""
from fashion_clip.fashion_clip import FashionCLIP

# 전역 상태
fclip: FashionCLIP | None = None


def load_all():
    """Fashion CLIP 모델을 로드합니다."""
    global fclip

    print("[startup] Fashion CLIP 모델 로딩 중...")
    fclip = FashionCLIP("fashion-clip")
    print(f"[startup] Fashion CLIP 로드 완료")


def get_fclip() -> FashionCLIP:
    """로드된 Fashion CLIP 인스턴스를 반환합니다."""
    if fclip is None:
        raise RuntimeError("Fashion CLIP 모델이 아직 로드되지 않았습니다.")
    return fclip