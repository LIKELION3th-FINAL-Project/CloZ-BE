import os
import sys
import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.image_utils import download_image_bytes_from_url
from app.s3 import (
    generate_presigned_image_url,
    get_s3_client,
    upload_generated_output,
)
from app.schemas.agent import AgentRequest, AgentResponse, OutfitInfo, ProductInfo
from app.state import get_clip_encoder, get_understand_model
from generation_pipeline.understand_model.understand_model import (
    build_system_prompt,
    build_user_prompt,
    extract_json_format,
)

import logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["agent"])
_generation_model = None


def _ensure_models_src_on_path():
    models_src = f"{settings.MODELS_ROOT}/"
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
    image_url = None
    if image_key:
        try:
            image_url = generate_presigned_image_url(image_key)
        except Exception as exc:
            logger.warning(
                "presigned URL 생성 실패 (image_key=%s): %s",
                image_key,
                exc,
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
        image_url=image_url,
        products=products,
    )


async def _fetch_closet_from_db(user_id: int, session: AsyncSession) -> dict: 
    
    # closet_closet 테이블에서 사용자 옷장 아이템을 직접 조회회
    # embedding_status = 'ONE이고 embedding이 있는 아이템만 반환됨
    
    result = await session.execute(
        text("""
            SELECT id, category, embedding::text, style_cat,image
            FROM closet_closet
            WHERE user_id = :user_id
              AND embedding_status = 'DONE'
              AND embedding IS NOT NULL
        """),
        {"user_id": user_id},
    )
    rows = result.fetchall()

    closet_data: dict = {"TOP": [], "BOTTOM": [], "OUTER": []}
    for row in rows:
        closet_id, category, embedding_text, style_cat, image = row
        try:
            embedding = json.loads(embedding_text)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(embedding, list) or len(embedding) != 512:
            continue
        if category not in closet_data:
            continue
        closet_data[category].append({
            "id": str(closet_id),
            "image_url": image or "",  # "closet_images/bottoms_5.jpeg" 형태로 채워짐
            "style_cat": style_cat or "",
            "embedding": embedding,
        })

    logger.info(
        "[closet_db] user_id=%s → TOP=%d, BOTTOM=%d, OUTER=%d",
        user_id,
        len(closet_data["TOP"]),
        len(closet_data["BOTTOM"]),
        len(closet_data["OUTER"]),
    )
    return closet_data


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

def _interact_with_user_chat(understand_model, first_model_response: str) -> str:  # 호출해서 쓰는거 고려. 
    """
    models/ 코드를 수정하지 않고, A(=initial_chat 결과)를 입력으로 받아
    B(=interact_with_user_chat 결과)를 생성한다.
    """
    messages = [
        build_system_prompt(understand_model.interact_with_user_sys_prompt, first_model_response)
    ]
    # user prompt는 선택 사항이지만, 빈 문자열이면 일부 백엔드에서 거부될 수 있어 공백을 넣는다.
    messages.append(build_user_prompt(" "))

    response = understand_model.client.chat.completions.create(
        model=understand_model.model_name,
        messages=messages,
        temperature=understand_model.temperature,
        reasoning_effort=understand_model.reasoning_effort,
    )
    return response.choices[0].message.content


@router.post("/agents/", response_model=AgentResponse)
async def run_agent(
    req: AgentRequest,
    session: AsyncSession = Depends(get_session),
): #closet 데이터 우선순위 로직 추가
    logger.info("에이전트 요청 시작")
    try:
        understand_model = get_understand_model()
        model_input = _build_agent_prompt(req)  
        logger.info("에이전트 요청 :  session=%s user=%s msg=%r body_image_url=%r",req.session_id, req.user.user_id, req.message[:200], req.user.body_image_url)

        # 1) A = initial_chat(user input 기반)
        initial_output = understand_model.initial_chat(model_input)
        logger.info("A(initial_chat) 결과: %s", initial_output)

        # 2) B = interact_with_user_chat(A)
        interact_output = _interact_with_user_chat(understand_model, initial_output)
        logger.info("B(interact_with_user_chat) 결과: %s", interact_output)

        # 2) JSON 파싱 시도
        parsed = extract_json_format(interact_output)
        logger.info("JSON 파싱 결과: %s", parsed)

        # 3) 프론트 표시용: 파싱 성공하면 pretty json, 실패하면 raw text
        if parsed is not None:
            message_text = json.dumps(parsed, ensure_ascii=False, indent=2)
        else:
            message_text = interact_output
        logger.info("프론트 표시용 메시지: %s", message_text)
        generation_outfits = []
        generation_model = _get_generation_model()
        tmp_body_image_path = None

        # closet 데이터 준비:
        # req.closet에 임베딩이 있으면 그걸 사용, 없으면 DB에서 직접 조회
        req_items_with_emb = [
            item
            for items in [req.closet.TOP, req.closet.BOTTOM, req.closet.OUTER]
            for item in items
            if item.embedding
        ]
        if req_items_with_emb:
            closet_data = {
                scope: [item.model_dump() for item in items]
                for scope, items in [
                    ("TOP", req.closet.TOP),
                    ("BOTTOM", req.closet.BOTTOM),
                    ("OUTER", req.closet.OUTER),
                ]
                if items
            }
            logger.info("[closet] req에서 closet 사용 (아이템 수: %d)", len(req_items_with_emb))
        else:
            closet_data = await _fetch_closet_from_db(req.user.user_id, session)
        
        # closet 이미지 S3 → 로컬 임시 파일 다운로드
        tmp_closet_files: list = []
        s3 = get_s3_client()
        for scope_items in closet_data.values():
            for item in scope_items:
                s3_key = item.get("image_url", "")
                if not s3_key:
                    continue
                try:
                    suffix = Path(s3_key).suffix or ".jpg"
                    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                        s3.download_fileobj(settings.AWS_S3_BUCKET_NAME, s3_key, tmp)
                        item["image_url"] = tmp.name
                        tmp_closet_files.append(tmp.name)
                    logger.info("[closet] S3 다운로드: %s → %s", s3_key, item["image_url"])
                except Exception as e:
                    logger.warning("[closet] S3 다운로드 실패 (빈 경로로 진행): %s → %s", s3_key, e)
                    item["image_url"] = ""

        generation_context: dict = {"closet_data": closet_data}

        try:
            if req.user.body_image_url:
                if req.user.body_image_url.startswith("http"):
                    try:
                        image_bytes = await download_image_bytes_from_url(req.user.body_image_url)
                    except Exception as exc:
                        raise HTTPException(
                            status_code=400,
                            detail=f"body_image_url 다운로드 실패: {exc}",
                        ) from exc
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                        tmp.write(image_bytes)
                        tmp_body_image_path = tmp.name
                    generation_model.config["user_body_image"] = tmp_body_image_path
                else:
                    generation_model.config["user_body_image"] = req.user.body_image_url

            has_closet = any(generation_context["closet_data"].values())
            generation_result = generation_model.generate(
                prompt=req.message,
                user_id=str(req.user.user_id),
                context=generation_context if has_closet else None,
            )
        finally:
            if tmp_body_image_path and os.path.exists(tmp_body_image_path):
                os.unlink(tmp_body_image_path)
            for p in tmp_closet_files:
                if os.path.exists(p):
                    os.unlink(p)

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