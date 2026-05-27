"""POST /api/calculate — 가산점 계산 엔드포인트 (PRD REQ-004, SRS UC-004)"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, BonusRule
from app.engine.rule_engine import (
    CertInput, LanguageScores, BonusRuleItem,
    CompanyRuleSet, run_engine
)

router = APIRouter()


# ── Pydantic 요청/응답 스키마 ─────────────────────────────────────────────

class CertInputSchema(BaseModel):
    name: str
    grade: str


class LanguageScoresSchema(BaseModel):
    toeic: Optional[int] = None
    toeic_speaking: Optional[str] = None
    opic: Optional[str] = None


class CalculateRequest(BaseModel):
    job_series: str                              # "사무직" | "기술직"
    certificates: List[CertInputSchema] = []
    language_scores: LanguageScoresSchema = LanguageScoresSchema()


class CompanyResultItem(BaseModel):
    company_id: int
    company_name: str
    my_bonus_score: float
    max_bonus_score: int
    match_rate: float
    feedback: Optional[str]


class CalculateResponse(BaseModel):
    job_series: str
    results: List[CompanyResultItem]


# ── 엔드포인트 ────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=CalculateResponse, summary="가산점 계산 요청")
async def calculate_bonus_score(
    request: CalculateRequest,
    db: Session = Depends(get_db),
):
    """
    사용자의 직렬·자격증·어학성적을 기반으로
    전체 공기업별 가산점 및 매칭률을 계산하여 반환합니다.
    """
    # 1. 해당 직렬 활성 기업 조회
    companies = (
        db.query(Company)
        .filter(
            Company.is_active == True,
            Company.series_type.in_(["공통", request.job_series])
        )
        .all()
    )

    if not companies:
        raise HTTPException(status_code=404, detail="해당 직렬에 등록된 공기업 데이터가 없습니다.")

    # 2. 기업별 룰셋 구성
    company_rule_sets: List[CompanyRuleSet] = []
    for company in companies:
        rules_db = (
            db.query(BonusRule)
            .filter(BonusRule.company_id == company.id)
            .all()
        )
        rules = [
            BonusRuleItem(
                id=r.id,
                company_id=r.company_id,
                category=r.category,
                certificate_name=r.certificate_name,
                grade=r.grade,
                score=r.score,
                calc_type=r.calc_type,
                base_score=r.base_score,
                series_filter=r.series_filter,
            )
            for r in rules_db
            if r.series_filter in ("공통", request.job_series)
        ]
        company_rule_sets.append(
            CompanyRuleSet(
                company_id=company.id,
                company_name=company.name,
                max_bonus_score=company.max_bonus_score,
                rules=rules,
            )
        )

    # 3. 룰 엔진 실행
    certs = [CertInput(name=c.name, grade=c.grade) for c in request.certificates]
    lang = LanguageScores(
        toeic=request.language_scores.toeic,
        toeic_speaking=request.language_scores.toeic_speaking,
        opic=request.language_scores.opic,
    )
    engine_results = run_engine(company_rule_sets, certs, lang)

    # 4. 응답 변환
    results = [
        CompanyResultItem(
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
