"""
Celery 워커 설정
- Redis를 브로커/백엔드로 사용
- app.tasks 모듈의 태스크를 자동 탐색
"""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# 태스크 모듈 자동 탐색
celery_app.autodiscover_tasks(["app.tasks"])

# Celery 설정
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Seoul",
    enable_utc=True,
)
