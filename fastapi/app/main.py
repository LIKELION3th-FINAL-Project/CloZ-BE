from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import agent, embedding
from app.state import load_all
from app.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 시작 ──
    load_all()                          # Fashion CLIP 모델 로드

    # DB 연결 확인
    async with engine.connect() as conn:
        await conn.execute("SELECT 1")
    print("[startup] DB 연결 확인 완료")

    yield

    # ── 종료 ──
    await engine.dispose()              # DB 커넥션 풀 정리
    print("[shutdown] 리소스 정리 완료")


app = FastAPI(lifespan=lifespan)        # lifespan 연결!

# 라우터
app.include_router(agent.router, prefix="/api")
app.include_router(embedding.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
