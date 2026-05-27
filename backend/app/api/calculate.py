"""POST /api/calculate - 가산점 계산 API (PRD REQ-001~005)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.engine.rule_engine import CertInput, LanguageScores, run_engine
from app.services.bonus_service import get_companies_with_rules

router = APIRouter()

# ── Pydantic 스키마 ───────────────────────────────────────────────────────

VALID_JOB_SERIES = [
    # ── 일반직 ──
    "행정", "사무", "기술",
    # ── 전력·에너지 기술직 ──
    "전기", "기계", "화학", "전기통신",
    # ── IT ──
    "IT", "ICT",
    # ── 건설 ──
    "토목", "건축", "건설",
    # ── 철도 특수직 ──
    "사무영업·열차승무", "운전", "차량",
    # ── 하위 호환 ──
    "사무직", "기술직",
]

VALID_OPIC = ["NL", "IL", "IM1", "IM2", "IM3", "IH", "AL"]
VALID_TOEIC_SPEAKING = ["Lv.1", "Lv.2", "Lv.3", "Lv.4", "Lv.5", "Lv.6", "Lv.7", "Lv.8"]


class CertificateInput(BaseModel):
    name: str
    grade: str

    @field_validator("name", "grade")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("자격증 이름과 급수는 필수 항목입니다.")
        return v.strip()


class LanguageScoreInput(BaseModel):
    toeic: Optional[int] = None
    toeic_speaking: Optional[str] = None
    opic: Optional[str] = None

    @field_validator("toeic")
    @classmethod
    def validate_toeic(cls, v):
        if v is not None and not (0 <= v <= 990):
            raise ValueError("toeic 점수는 0~990 범위여야 합니다.")
        return v

    @field_validator("toeic_speaking")
    @classmethod
    def validate_toeic_speaking(cls, v):
        if v is not None and v not in VALID_TOEIC_SPEAKING:
            raise ValueError(f"토익스피킹 등급은 {VALID_TOEIC_SPEAKING} 중 하나여야 합니다.")
        return v

    @field_validator("opic")
    @classmethod
    def validate_opic(cls, v):
        if v is not None and v not in VALID_OPIC:
            raise ValueError(f"OPIc 등급은 {VALID_OPIC} 중 하나여야 합니다.")
        return v


class CalculateRequest(BaseModel):
    job_series: str
    certificates: list[CertificateInput] = []
    language_scores: Optional[LanguageScoreInput] = None

    @field_validator("job_series")
    @classmethod
    def validate_job_series(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("job_series는 필수 항목입니다.")
        if v.strip() not in VALID_JOB_SERIES:
            raise ValueError(f"job_series는 {VALID_JOB_SERIES} 중 하나여야 합니다.")
        return v.strip()

    @model_validator(mode="after")
    def check_at_least_one_spec(self) -> "CalculateRequest":
        has_cert = bool(self.certificates)
        has_lang = (
            self.language_scores is not None and (
                self.language_scores.toeic is not None or
                self.language_scores.toeic_speaking is not None or
                self.language_scores.opic is not None
            )
        )
        if not has_cert and not has_lang:
            raise ValueError("자격증 또는 어학 성적 중 최소 1개 이상 입력해야 합니다.")
        return self


class MatchResultItem(BaseModel):
    company_id: int
    company_name: str
    my_bonus_score: float
    max_bonus_score: int
    match_rate: float
    feedback: Optional[str]


class CalculateResponse(BaseModel):
    job_series: str
    results: list[MatchResultItem]


# ── 엔드포인트 ────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=CalculateResponse, summary="공기업 가산점 계산")
async def calculate_bonus_score(
    request: CalculateRequest,
    db: Session = Depends(get_db),
):
    """
    사용자 스펙(자격증·어학·직렬)을 입력받아 전체 공기업 가산점 및 매칭률을 계산합니다.

    - OR 룰: 동일 계열 자격증 중 최고 등급 1개만 반영
    - 어학 비례 연산: (유저점수 / 만점기준) × 배점
    - 합산 한도(Cap): 기업별 최대 가산점 초과분 절삭
    - 결과: 매칭률 내림차순 정렬
    """
    # DB에서 직렬 필터링된 공기업 + 룰 조회
    companies = get_companies_with_rules(db, request.job_series)

    if not companies:
        raise HTTPException(
            status_code=404,
            detail="현재 등록된 공기업 데이터가 없습니다."
        )

    # 엔진용 입력 데이터 변환
    cert_inputs = [
        CertInput(name=c.name, grade=c.grade)
        for c in request.certificates
    ]
    lang_scores = LanguageScores(
        toeic=request.language_scores.toeic if request.language_scores else None,
        toeic_speaking=request.language_scores.toeic_speaking if request.language_scores else None,
        opic=request.language_scores.opic if request.language_scores else None,
    )

    # 룰 엔진 실행 (개별 기업 오류 시 스킵 — SRS 6.3)
    engine_results = run_engine(companies, cert_inputs, lang_scores)

    results = [
        MatchResultItem(
            company_id=r.company_id,
            company_name=r.company_name,
            my_bonus_score=r.my_bonus_score,
            max_bonus_score=r.max_bonus_score,
            match_rate=r.match_rate,
            feedback=r.feedback,
        )
        for r in engine_results
    ]

    return CalculateResponse(job_series=request.job_series, results=results)
