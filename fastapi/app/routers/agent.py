import sys
import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.image_utils import download_image_bytes_from_url
from app.s3 import upload_generated_output
from app.schemas.agent import AgentRequest, AgentResponse, OutfitInfo, ProductInfo
from app.state import get_clip_encoder, get_understand_model
from generation_pipeline.understand_model.understand_model import extract_json_format

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])
_generation_model = None


def _ensure_models_src_on_path():
    models_src = f"{settings.MODELS_ROOT}/src"
    if models_src not in sys.path:
        sys.path.insert(0, models_src)


def _get_generation_model():
    global _generation_model
    if _generation_model is not None:
        return _generation_model

    _ensure_models_src_on_path()

    from generation_pipeline.fashion_engine.recommender import FashionRecommender
    from generation_pipeline.fashion_engine.planner import OutfitPlanner
    from generation_pipeline.fashion_engine.vton import VTONManager
    from generation_pipeline.utils.load import load_config
    from feedback_pipeline.interfaces.real_generation_model import RealGenerationModel

    encoder = get_clip_encoder()
    understand_model = get_understand_model() # llm호출 
    config = load_config(settings.generation_config_path)

    _generation_model = RealGenerationModel(
        understand_model=understand_model,
        encoder=encoder,
        recommender=FashionRecommender(encoder),
        planner=OutfitPlanner(encoder),
        vton=VTONManager(),
        config=config,
    )
    return _generation_model


def _resolve_image_key(image_source: str, user_id: int, session_id: str) -> str:
    if not image_source:
        raise ValueError("model output image source is empty")
    if image_source.startswith("recommendations/"):
        return image_source

    image_path = Path(image_source)
    if image_path.exists() or not image_source.startswith("http"):
        return upload_generated_output(
            user_id=user_id,
            session_id=session_id,
            local_output_path=image_source,
        )
    raise ValueError(f"unsupported model output for image_key contract: {image_source}")


def _to_outfit_info(model_outfit, user_id: int, session_id: str) -> OutfitInfo:
    image_key = _resolve_image_key(
        image_source=getattr(model_outfit, "image_url", ""),
        user_id=user_id,
        session_id=session_id,
    )
    products = [
        ProductInfo(
            product_id=item.product_id,
            category_main=item.category_main,
            category_sub=item.category_sub,
            product_name=item.product_name,
        )
        for item in getattr(model_outfit, "products", [])
    ]
    return OutfitInfo(
        outfit_id=getattr(model_outfit, "outfit_id", 0),
        image_key=image_key,
        products=products,
    )


def _build_agent_prompt(req: AgentRequest) -> str:
    """
    UnderstandModel에 전달할 프롬프트를 구성한다.
    body_image_url이 있으면 모델이 참고할 수 있도록 컨텍스트를 덧붙인다.
    """
    if req.user.body_image_url:
        return (
            f"{req.message}\n\n"
            "[SYSTEM_CONTEXT]\n"
            f"user_body_image_url: {req.user.body_image_url}"
        )

    return (
        f"{req.message}\n\n"
        "[SYSTEM_CONTEXT]\n"
        "user_body_image_url: NONE"
    )


@router.post("/agents/", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    logger.info("에이전트 요청 시작")
    try:
        understand_model = get_understand_model()
        model_input = _build_agent_prompt(req)  
        logger.info("에이전트 요청 :  session=%s user=%s msg=%r body_image_url=%r",req.session_id, req.user.user_id, req.message[:200], req.user.body_image_url)

        # 1) LLM 원문 응답
        raw_output = understand_model.initial_chat(model_input)
        logger.info("LLM 원문 응답: %s", raw_output)

        # 2) JSON 파싱 시도
        parsed = extract_json_format(raw_output)
        logger.info("JSON 파싱 결과: %s", parsed)

        # 3) 프론트 표시용: 파싱 성공하면 pretty json, 실패하면 raw text
        if parsed is not None:
            message_text = json.dumps(parsed, ensure_ascii=False, indent=2)
        else:
            message_text = raw_output
        logger.info("프론트 표시용 메시지: %s", message_text)
        generation_outfits = []
        generation_model = _get_generation_model()
        generation_context = {}

        if req.user.body_image_url and req.user.body_image_url.startswith("http"):
            try:
                generation_context["user_body_image_bytes"] = (
                    await download_image_bytes_from_url(req.user.body_image_url)
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"body_image_url 다운로드 실패: {exc}",
                ) from exc

        # 요청에서 전달된 경로가 로컬 파일 경로면 동적으로 반영한다.
        if req.user.body_image_url and not req.user.body_image_url.startswith("http"):
            generation_model.config["user_body_image"] = req.user.body_image_url

        generation_result = generation_model.generate(
            prompt=req.message,
            user_id=str(req.user.user_id),
            context=generation_context or None,
        )
        if generation_result.success and generation_result.outfits:
            generation_outfits = [
                _to_outfit_info(
                    model_outfit=o,
                    user_id=req.user.user_id,
                    session_id=req.session_id or "default",
                )
                for o in generation_result.outfits
            ]

        return AgentResponse(
            session_id=req.session_id,
            message=message_text,
            outfits=generation_outfits,
        )

    except RuntimeError as e:
        # model not loaded
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"agent 처리 실패: {e}")