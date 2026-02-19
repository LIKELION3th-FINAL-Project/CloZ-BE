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

    # ── 서브모듈(CloZ-AI) 경로 ──
    # Docker 컨테이너 내 마운트 경로
    MODELS_ROOT: str = "/app/models"

    # ── Fashion CLIP (이미지 임베딩 + 스타일 분류) ──
    # generation_model.yaml의 model_name과 동일
    CLIP_MODEL_NAME: str = "patrickjohncyh/fashion-clip"
    EMBEDDING_DIM: int = 512

    # ── LLM (Upstage Solar Pro3 API) ──
    UPSTAGE_API_KEY: str = ""

    # ── AWS S3 ──
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET_NAME: str = ""
    AWS_S3_REGION_NAME: str = "ap-northeast-2"

    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def celery_result_backend(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def generation_config_path(self) -> str:
        return f"{self.MODELS_ROOT}/configs/generation_model.yaml"

    @property
    def llm_config_path(self) -> str:
        return f"{self.MODELS_ROOT}/configs/llm_base_understand.yaml"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra ="ignore"


settings = Settings()
