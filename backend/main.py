"""
공기업 가산점 자동 계산 및 매칭 시스템 — FastAPI 메인 애플리케이션
PRD.md / TASK.md / 요구사항명세서.md 기반 구현
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# DB 초기화 및 시드 데이터 삽입
from app.database import engine
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 DB 테이블 생성 및 시드 데이터 삽입"""
    logger.info("공기업 가산점 매칭 시스템 시작")
    Base.metadata.create_all(bind=engine)
    logger.info("DB 테이블 생성 완료")

    # 실제 공기업 데이터 삽입 (공기업 자격증.md 기반)
    try:
        from seed_data_real import seed_real
        seed_real()
    except Exception as e:
        logger.warning(f"실제 데이터 삽입 실패, 샘플 데이터로 폴백: {e}")
        try:
            from seed_data import seed
            seed()
        except Exception as e2:
            logger.warning(f"샘플 데이터 삽입 중 오류 (무시): {e2}")

    yield
    logger.info("🛑 서버 종료")


# FastAPI 앱 생성
app = FastAPI(
    title="공기업 가산점 자동 계산 및 매칭 시스템",
    description=(
        "취업 준비생이 보유한 자격증·어학 스펙을 입력하면 "
        "전국 공기업별 가산점을 자동으로 계산하고 매칭률 기반으로 추천합니다."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 설정 (프론트엔드 연동)
cors_origins_env = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
origins += ["http://localhost:8000", "http://127.0.0.1:8000", "null"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 예외 핸들러 (SRS 6.3 - Python 프로세스 크래시 방지)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"전역 예외 발생: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "계산 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."}
    )

# 422 유효성 오류 핸들러
from fastapi.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for error in errors:
        field = " → ".join(str(loc) for loc in error["loc"])
        messages.append(f"{field}: {error['msg']}")
    return JSONResponse(
        status_code=422,
        content={"error": " | ".join(messages)}
    )

# API 라우터 등록
from app.api import calculate, companies, admin

app.include_router(calculate.router, prefix="/api", tags=["가산점 계산"])
app.include_router(companies.router, prefix="/api", tags=["공기업 목록"])
app.include_router(admin.router, prefix="/api", tags=["관리자"])

# 프론트엔드 정적 파일 서빙
frontend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")


@app.get("/health", tags=["시스템"])
async def health_check():
    """서버 상태 확인"""
    return {"status": "ok", "service": "공기업 가산점 매칭 시스템"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
