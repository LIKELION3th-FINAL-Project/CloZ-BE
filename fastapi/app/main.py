from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.routers import agent, embedding
from app.state import get_model_status, load_all
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):

    # 모델 로딩 실패가 있어도 API 서버 자체는 뜨도록 처리한다.
    load_all()
    app.state.model_status = get_model_status()
    if app.state.model_status["errors"]:
        print(f"[startup][warn] model load errors: {app.state.model_status['errors']}")

    # DB 연결 확인
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    print("[startup] DB 연결 확인 완료")

    yield


    await engine.dispose()              # DB 커넥션 풀 정리
    print("[shutdown] 리소스 정리 완료")


app = FastAPI(lifespan=lifespan)

# 라우터
app.include_router(embedding.router, prefix="/ai")
app.include_router(agent.router, prefix="/ai")


@app.get("/ai/health")
def health_check():
    return {"status": "ok"}


@app.get("/ready")
def readiness_check():
    model_status = get_model_status()
    if model_status["clip_encoder_loaded"] and model_status["understand_model_loaded"]:
        return {"status": "ready", "models": model_status}
    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "models": model_status},
    )
