"""
Fashion CLIP zero-shot 스타일 분류
- CLIPEncoder의 encode_image / encode_text를 사용
- 이미지 임베딩과 스타일 텍스트 임베딩의 코사인 유사도 비교
- 가장 유사한 스타일 카테고리를 반환
"""
import torch

# 분류할 스타일 카테고리 목록
STYLE_LABELS: list[str] = [
    "캐주얼",
    "포멀",
    "스트릿",
    "스포티",
    "리조트",
    "빈티지",
    "미니멀",
    "로맨틱",
]


def classify_style(encoder, image_path: str) -> str:
    """
    이미지 → CLIPEncoder zero-shot 분류 → 스타일 레이블 반환.

    Args:
        encoder: CLIPEncoder 인스턴스 (서브모듈)
        image_path: 이미지 파일 경로

    Returns:
        가장 유사한 스타일 레이블 문자열 (예: "리조트")
    """
    # 이미지 임베딩 (512차원, 정규화 済)
    image_emb = encoder.encode_image(image_path)

    # 각 스타일 레이블의 텍스트 임베딩을 하나씩 구해 스택
    text_prompts = [f"{label} 스타일 의류" for label in STYLE_LABELS]
    text_embs = torch.stack([
        encoder.encode_text(prompt) for prompt in text_prompts
    ])

    # 코사인 유사도 (CLIPEncoder._extract_features에서 이미 정규화됨)
    similarities = (image_emb @ text_embs.T).squeeze()

    best_idx = int(torch.argmax(similarities))
    return STYLE_LABELS[best_idx]
