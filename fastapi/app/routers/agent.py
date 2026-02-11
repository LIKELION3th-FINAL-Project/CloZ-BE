from fastapi import APIRouter

router = APIRouter(tags=["agent"])


@router.post("/agents/")
async def run_agent():
    """AI 에이전트 실행 엔드포인트 (TODO: 구현)"""
    return {"message": "agent endpoint"}
