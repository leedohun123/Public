"""GET /api/companies, GET /api/companies/{id}/rules (PRD REQ-003)"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, BonusRule

router = APIRouter()


# ── Pydantic 스키마 ───────────────────────────────────────────────────────

class CompanyItem(BaseModel):
    id: int
    name: str
    series_type: str
    max_bonus_score: int
    is_active: bool

    model_config = {"from_attributes": True}


class BonusRuleItem(BaseModel):
    id: int
    company_id: int
    category: str
    certificate_name: str
    grade: str
    score: float
    calc_type: str
    base_score: Optional[int]
    series_filter: str

    model_config = {"from_attributes": True}


# ── 엔드포인트 ────────────────────────────────────────────────────────────

@router.get("/companies", response_model=list[CompanyItem], summary="공기업 목록 조회")
async def get_companies(
    series: Optional[str] = Query(None, description="직렬 필터: 사무직 또는 기술직"),
    db: Session = Depends(get_db),
):
    """
    전체 공기업 목록을 조회합니다.
    - `?series=사무직` 또는 `?series=기술직` 파라미터로 필터링 가능
    - is_active=False 기업은 자동 제외
    """
    query = db.query(Company).filter(Company.is_active == True)
    if series:
        query = query.filter(Company.series_type.in_(["공통", series]))
    companies = query.order_by(Company.name).all()
    return companies


@router.get("/companies/{company_id}/rules", response_model=list[BonusRuleItem], summary="공기업 가산점 룰 상세 조회")
async def get_company_rules(
    company_id: int,
    db: Session = Depends(get_db),
):
    """
    특정 공기업의 전체 가산점 룰 목록을 조회합니다.
    존재하지 않는 company_id 요청 시 404 반환.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="해당 공기업을 찾을 수 없습니다.")

    rules = (
        db.query(BonusRule)
        .filter(BonusRule.company_id == company_id)
        .order_by(BonusRule.category, BonusRule.score.desc())
        .all()
    )
    return rules
