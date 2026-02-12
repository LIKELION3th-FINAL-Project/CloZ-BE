from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── PostgreSQL ──
    POSTGRES_USER: str = "app"
    POSTGRES_PASSWORD: str = "app1234"
    POSTGRES_DB: str = "appdb"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432

    # ── Redis ──
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    # ── 모델 설정 ──
    CLIP_MODEL_NAME: str = "patrickjohncyh/fashion-clip"
    EMBEDDING_DIM: int = 512

    @property
    def database_url(self) -> str:
        """asyncpg용 비동기 DB URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    class Config:
        env_file = ".env"          # 로컬 개발 시 .env 파일도 지원
        case_sensitive = True

    # ── AWS S3 ──
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_REGION_NAME: str = "ap-northeast-2"
    
settings = Settings()