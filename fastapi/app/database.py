from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

# 비동기 엔진
engine = create_async_engine(
    settings.database_url,
    echo=False,            # True로 하면 SQL 로그 출력
    pool_size=5,
    max_overflow=10,
)

# 세션 팩토리
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_session():
    """FastAPI Depends용 세션 제너레이터"""
    async with AsyncSessionLocal() as session:
        yield session