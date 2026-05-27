"""FastAPI 앱 진입점 (공기업 가산점 매칭 시스템)"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import companies, admin
from app.api import calculate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 생성 + 시드 데이터 삽입"""
    logger.info("앱 시작: DB 초기화 중...")
    Base.metadata.create_all(bind=engine)

    # 시드 데이터 삽입 (DB가 비어있을 때만)
    from app.services.seed import seed_initial_data
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        seed_initial_data(db)
    finally:
        db.close()

    logger.info("DB 초기화 완료")
    yield
    logger.info("앱 종료")


app = FastAPI(
    title="공기업 가산점 매칭 시스템",
    description="공기업 채용 시험 가산점 자동 계산 API",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS 설정 ────────────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "https://public-bqsf.vercel.app,http://localhost:3000,http://127.0.0.1:5500,http://127.0.0.1:8000"
).split(",")

# 개발 편의상 와일드카드 허용 (프로덕션에서는 명시적 도메인 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 라우터 등록 ──────────────────────────────────────────────────────────
app.include_router(companies.router, prefix="/api", tags=["companies"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(calculate.router, prefix="/api", tags=["calculate"])


@app.get("/", tags=["health"])
async def root():
    return {"status": "ok", "message": "공기업 가산점 매칭 시스템 API"}


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}
