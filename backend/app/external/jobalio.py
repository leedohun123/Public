"""
외부 API 연동 레이어 — 잡알리오(JOB ALIO) / 공공데이터포털 (SRS 5.3)
독립 레이어로 분리하여 API 변경 시 영향 범위 최소화 (SRS 6.4)

API 키 미설정 또는 연동 실패 시 오류를 raise하여 호출 측에서 처리하도록 설계.
"""
import os
import logging
import httpx
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

JOBALIO_API_KEY = os.getenv("JOBALIO_API_KEY", "")
PUBLIC_DATA_API_KEY = os.getenv("PUBLIC_DATA_API_KEY", "")

# 잡알리오 API 기본 URL (실제 운영 시 공식 문서 확인)
JOBALIO_BASE_URL = "https://openapi.gg.go.kr/JOBALIO"


async def fetch_jobalio_data() -> dict:
    """
    잡알리오 API에서 공기업 채용 공고 데이터를 가져옵니다.
    실제 운영 시 API 키를 .env에 설정하세요.
    """
    if not JOBALIO_API_KEY or JOBALIO_API_KEY == "demo_key":
        raise ValueError(
            "JOBALIO_API_KEY가 설정되지 않았습니다. "
            ".env 파일에 실제 API 키를 입력하세요."
        )

    params = {
        "KEY": JOBALIO_API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(JOBALIO_BASE_URL, params=params)
        response.raise_for_status()
        return response.json()


async def sync_from_external_api(db: Session) -> str:
    """
    외부 API(잡알리오 등)에서 데이터를 가져와 DB를 갱신합니다.
    실패 시 예외를 raise (호출 측에서 오류 로그 기록 후 기존 DB 유지).
    """
    logger.info("[External] 외부 API 동기화 시작")

    try:
        data = await fetch_jobalio_api_safe()
        # 실제 연동 시 여기서 data를 파싱하여 DB 업데이트
        # 현재는 Demo 모드로 실제 API 호출 없이 메시지만 반환
        logger.info("[External] 외부 API 동기화 완료 (Demo 모드)")
        return "Demo 모드: 실제 API 키 설정 후 동기화 가능"
    except Exception as e:
        logger.error(f"[External] API 호출 실패: {e}")
        raise


async def fetch_jobalio_api_safe() -> dict:
    """
    잡알리오 API 호출 (Demo 모드: API 키 미설정 시 Mock 데이터 반환)
    실제 운영 시 fetch_jobalio_data()로 교체하세요.
    """
    if not JOBALIO_API_KEY or JOBALIO_API_KEY in ("demo_key", ""):
        logger.warning("[External] API 키 미설정 — Demo 모드로 동작")
        return {"status": "demo", "message": "API 키를 설정하면 실제 데이터를 동기화합니다."}

    return await fetch_jobalio_data()
