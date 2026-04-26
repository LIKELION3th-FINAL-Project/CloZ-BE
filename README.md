<h1 align="left">AI 추천 패션 커머스 서비스</h1>

입력 프롬프트와 개인 옷장 이미지를 기반으로 코디를 추천하는 패션 커머스 서비스입니다.

<img src="./readme용 서비스미리보기.png" width="850" height="850"/>

- **배포 URL** : [https://clo-z-fe.vercel.app/](https://clo-z-fe.vercel.app/)

---

<h2 align="left">📖 프로젝트 소개</h2>

- 온라인에서 옷을 고르고 기존 옷과 코디할 때, 취향과 상황에 맞는 코디를 빠르게 확인하기 어렵다는 점에서 출발한 서비스입니다. 
- 상품 조회부터 장바구니, 주문, 결제까지 이어지는 커머스 기능과 옷장 이미지를 기반으로 임베딩 및 스타일 분류를 통해 코디를 추천하는 AI 기능이 있습니다. 
- 코디 추천은 LLM기반 이해 모듈로 사용자 입력을 해석하고, 추천·플래닝·가상 착장(VTON) 파이프라인을 거쳐 이미지 형태의 결과로 제공합니다.
- 직관적인 페이지 흐름으로 설계하여 별도의 앱 설치 없이 브라우저 환경에서 서비스를 이용할 수 있습니다. 

---

<h2 align="left">✨ 주요 기능</h2>

- **회원 관리 & 소셜 로그인** : Kakao, Naver, Google, Email/Password  
- **옷장 관리** : 옷장 아이템 등록/ 조회/ 삭제
- **상품 및 쇼핑** : 상품 목록/ 카테고리/ 검색/ 상세, 장바구니 CRUD
- **주문 및 결제** : 주문과 1:1 연결된 결제
- **AI 코디 및 가상 착장** :  
  옷장 이미지 URL → Fashion CLIP 임베딩 및 스타일 분류 → DB 저장  
  사용자 입력 → LLM(UnderstandModel)기반 이해모듈 → 추천/ 플래닝/ VTON 파이프라인 → 결과 이미지 → S3 저장 → presigned URL 형태로 응답 

---

<h2 align="left">🎞️ 시연 영상</h2>

<!-- [![이미지](썸네일URL)](영상URL) -->

---

<h2 align="left">🖼️ 아키텍처 다이어그램</h2>

<img src="./readme용 아키텍처.png" width="1100"/>

---

<h2 align="left">📁 프로젝트 구조</h2>

```
CloZ-BE/
├── drf/                    # Django REST API (포트 8000)
│   ├── cloz/               # 프로젝트 설정 (settings.py, urls.py, wsgi.py)
│   ├── user/               # 사용자 인증, 소셜 로그인, 주소
│   ├── product/            # 상품 목록, 카테고리, 검색
│   ├── cart/               # 장바구니
│   ├── closet/             # 옷장 (사용자 소유 의류 아이템)
│   ├── order/              # 주문
│   ├── payment/            # 결제 (Toss Payments)
│   └── Dockerfile          # python:3.11-slim 기반
│
├── fastapi/                # AI 서비스 (포트 8001)
│   ├── app/
│   │   ├── main.py         # FastAPI 진입점, lifespan(모델 로딩+DB확인)
│   │   ├── config.py       # Pydantic BaseSettings (PostgreSQL/Redis/AWS/CLIP/LLM)
│   │   ├── database.py     # SQLAlchemy async engine
│   │   ├── state.py        # 모델 로딩 상태 관리
│   │   ├── worker.py       # Celery 앱 정의
│   │   ├── routers/
│   │   │   ├── agent.py     # POST /ai/agents/ — 패션 에이전트 (추천+VTON)
│   │   │   ├── embedding.py # POST /ai/embeddings/ — CLIP 임베딩+스타일 분류
│   │   │   └── images.py   # 생성 이미지 업로드/presigned URL
│   │   └── schemas/        # Pydantic 요청/응답 스키마
│   └── Dockerfile          # nvidia/cuda:12.1 기반 (GPU 지원)
│
├── models/                 # CloZ-AI 서브모듈 (git submodule)
│   ├── configs/            # generation_model.yaml, llm_base_understand.yaml
│   ├── src/
│   │   ├── generation_pipeline/  # 이미지 생성 파이프라인 (VTON 등)
│   │   └── feedback_pipeline/    # 피드백 루프 CLI (main.py)
│   └── pyproject.toml      # Ruff + pytest 설정
│
├── nginx/nginx.conf        # 리버스 프록시 설정
├── prometheus/             # Prometheus 설정 + 알림 규칙
├── alertmanager/           # Alertmanager 설정
├── data/                   # 제품 CSV, 임베딩 CSV, 상품 이미지
└── docker-compose.yml      # 전체 서비스 오케스트레이션


CloZ-FE/
└── frontend/              
   ├── src/
   │   ├── main.tsx        # React 진입점 (BrowserRouter 래핑)
   │   ├── App.tsx         # 라우트 정의 (10개 페이지)
   │   ├── api/            # Axios 기반 API 모듈 (8개 도메인별 파일)
   │   ├── components/     # UI 컴포넌트 (agent/, layout/ 등)
   │   ├── hooks/          # 커스텀 훅
   │   ├── pages/          # 페이지 컴포넌트
   │   ├── stores/         # Zustand 스토어 (authStore 등)
   │   └── types/          # TypeScript 타입 정의 (도메인별)
   └── vite.config.ts      # 개발 프록시 설정 포함
```

---

<h2 align="left">📚 기술 스택</h2>
<!-- Frontend -->
<h3 align="left">Frontend</h3>
<div align="left">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB">
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white">
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white">
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white">
  <img src="https://img.shields.io/badge/Zustand-443C34?style=for-the-badge&logo=zustand&logoColor=white">
  <img src="https://img.shields.io/badge/React_Router-CA4245?style=for-the-badge&logo=react-router&logoColor=white">
  <img src="https://img.shields.io/badge/Axios-5A29E4?style=for-the-badge&logo=axios&logoColor=white">
</div>

<!-- Backend -->
<h3 align="left">Backend</h3>
<div align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white">
  <img src="https://img.shields.io/badge/DRF-092E20?style=for-the-badge&logo=django&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/Uvicorn-2596BE?style=for-the-badge&logo=uvicorn&logoColor=white">
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white">
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white">
</div>

<!-- AI -->
<h3 align="left">AI / ML</h3>
<div align="left">
  <img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white">
  <img src="https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black">
  <img src="https://img.shields.io/badge/ChromaDB-FF6B6B?style=for-the-badge&logo=chromadb&logoColor=white">
  <img src="https://img.shields.io/badge/NVIDIA_CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white">
  <img src="https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white">
  <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini&logoColor=white">
</div>

<!-- infra -->
<h3 align="left">인프라 / 운영</h3>
<div align="left">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white">
  <img src="https://img.shields.io/badge/Oracle_Cloud-F80000?style=for-the-badge&logo=oracle&logoColor=white">
  <img src="https://img.shields.io/badge/Object_Storage_(S3_호환_API)-F80000?style=for-the-badge&logo=oracle&logoColor=white">
  <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white">
  <img src="https://img.shields.io/badge/Let's_Encrypt-003A70?style=for-the-badge&logo=letsencrypt&logoColor=white">
</div>

<!-- monitoring -->
<h3 align="left">모니터링</h3>
<div align="left">
  <img src="https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white">
  <img src="https://img.shields.io/badge/Grafana-F46800?style=for-the-badge&logo=grafana&logoColor=white">
  <img src="https://img.shields.io/badge/Alertmanager-E6522C?style=for-the-badge&logo=prometheus&logoColor=white">
</div>

---

<h2 align="left">▶️ 빠른 시작</h2>

### 환경 설정
```
git clone https://github.com/LIKELION3th-FINAL-Project/CloZ-BE.git
git clone https://github.com/LIKELION3th-FINAL-Project/CloZ-FE.git
cd CloZ-BE
git submodule update --init --recursive
docker compose build
```

### 서버 실행
```
# Backend & AI
cd CloZ-BE
docker compose up -d
docker compose exec app python manage.py migrate

# Frontend
cd CloZ-FE/frontend
npm install
npm run dev
```
⚠️ 실행 전 `.env` 파일 설정이 필요합니다.