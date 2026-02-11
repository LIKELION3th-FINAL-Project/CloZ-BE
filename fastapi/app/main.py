from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import agent, embedding
from app.state import load_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all()
    yield  


app = FastAPI()

# 라우터
app.include_router(agent.router, prefix="/api")
app.include_router(embedding.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
