from fastapi import APIRouter, HTTPException
import json

from app.schemas.agent import AgentRequest, AgentResponse
from app.state import get_understand_model
from generation_pipeline.understand_model.understand_model import extract_json_format

router = APIRouter(tags=["agent"])


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
    try:
        understand_model = get_understand_model()
        model_input = _build_agent_prompt(req)

        # 1) LLM 원문 응답
        raw_output = understand_model.initial_chat(model_input)

        # 2) JSON 파싱 시도
        parsed = extract_json_format(raw_output)

        # 3) 프론트 표시용: 파싱 성공하면 pretty json, 실패하면 raw text
        if parsed is not None:
            message_text = json.dumps(parsed, ensure_ascii=False, indent=2)
        else:
            message_text = raw_output

        return AgentResponse(
            session_id=req.session_id,
            message=message_text,
            outfits=[],
        )

    except RuntimeError as e:
        # model not loaded
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"agent 처리 실패: {e}")