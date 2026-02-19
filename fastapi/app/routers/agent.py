#/api/agents/ — 코디 추천 에이전트 엔드포인트

from fastapi import APIRouter

from app.schemas.agent import AgentRequest, AgentResponse

router = APIRouter(tags=["agent"])


@router.post("/agents/", response_model=AgentResponse)
async def run_agent(req: AgentRequest):
    """
    코디 추천 에이전트 실행.
    유저 정보, 옷장 데이터, 메시지를 기반으로 추론합니다.
    TODO: LLM + 임베딩 기반 추론 로직 구현
    """
    # TODO: 실제 추론 로직 구현
    # 1) req.closet의 이미지 임베딩 조회/활용
    # 2) req.message 분석 (LLM)
    # 3) 레퍼런스 임베딩과 유사도 비교
    # 4) 코디 조합 생성
    # 5) (선택) 코디 이미지 생성 → S3 업로드 → URL 반환

    return AgentResponse(
        session_id=req.session_id,
        message="아직 에이전트가 구현되지 않았습니다. 곧 멋진 코디를 추천해 드릴게요!",
        outfits=[],
    )
