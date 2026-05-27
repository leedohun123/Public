"""관리자 API (PRD REQ-007, SRS UC-007~008) — JWT 인증 필수"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, BonusRule, AdminLog
from app.auth import (
    authenticate_admin, create_access_token,
    get_current_admin, Token, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.external.jobalio import sync_from_external_api

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Pydantic 스키마 ───────────────────────────────────────────────────────

class BonusRuleUpdate(BaseModel):
    id: Optional[int] = None
    category: str
    certificate_name: str
    grade: str
    score: float
    calc_type: str = "FIXED"
    base_score: Optional[int] = None
    series_filter: str = "공통"


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    series_type: Optional[str] = None
    max_bonus_score: Optional[int] = None
    is_active: Optional[bool] = None
    bonus_rules: Optional[List[BonusRuleUpdate]] = None


class CompanyCreate(BaseModel):
    name: str
    series_type: str
    max_bonus_score: int
    is_active: bool = True
    bonus_rules: List[BonusRuleUpdate] = []


class CompanyResponse(BaseModel):
    id: int
    name: str
    series_type: str
    max_bonus_score: int
    is_active: bool

    model_config = {"from_attributes": True}


class AdminLogItem(BaseModel):
    id: int
    company_id: Optional[int]
    action: str
    changed_by: str
    detail: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncResponse(BaseModel):
    status: str
    message: str


# ── 인증 엔드포인트 ──────────────────────────────────────────────────────

@router.post("/admin/token", response_model=Token, summary="관리자 로그인 (JWT 발급)")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """관리자 로그인 후 JWT 액세스 토큰 발급"""
    if not authenticate_admin(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ── 관리자 전용 API (JWT 필수) ────────────────────────────────────────────

@router.get("/admin/companies", response_model=List[CompanyResponse], summary="관리자: 전체 공기업 목록")
async def admin_get_companies(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """관리자: 활성/비활성 포함 전체 공기업 목록 조회"""
    companies = db.query(Company).order_by(Company.id).all()
    return companies


@router.post("/admin/companies", response_model=CompanyResponse, summary="관리자: 공기업 신규 등록")
async def admin_create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """관리자: 새 공기업 등록"""
    existing = db.query(Company).filter(Company.name == company_data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="이미 등록된 공기업 이름입니다.")

    company = Company(
        name=company_data.name,
        series_type=company_data.series_type,
        max_bonus_score=company_data.max_bonus_score,
        is_active=company_data.is_active,
        updated_at=datetime.utcnow(),
    )
    db.add(company)
    db.flush()

    for rule_data in company_data.bonus_rules:
        rule = BonusRule(
            company_id=company.id,
            category=rule_data.category,
            certificate_name=rule_data.certificate_name,
            grade=rule_data.grade,
            score=rule_data.score,
            calc_type=rule_data.calc_type,
            base_score=rule_data.base_score,
            series_filter=rule_data.series_filter,
        )
        db.add(rule)

    # ADMIN_LOG 기록
    log = AdminLog(
        company_id=company.id,
        action="MANUAL_UPDATE",
        changed_by=current_admin,
        detail=f"신규 공기업 등록: {company.name}",
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(company)

    logger.info(f"[Admin] 공기업 신규 등록: {company.name} (by {current_admin})")
    return company


@router.put("/admin/companies/{company_id}", response_model=CompanyResponse, summary="관리자: 공기업 가산점 수동 업데이트")
async def admin_update_company(
    company_id: int,
    update_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """
    관리자: 특정 공기업 가산점 정보 수동 업데이트.
    ADMIN_LOG 테이블에 변경 이력 자동 기록.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="해당 공기업을 찾을 수 없습니다.")

    changes = []

    if update_data.name is not None:
        changes.append(f"name: {company.name} → {update_data.name}")
        company.name = update_data.name
    if update_data.series_type is not None:
        changes.append(f"series_type: {company.series_type} → {update_data.series_type}")
        company.series_type = update_data.series_type
    if update_data.max_bonus_score is not None:
        changes.append(f"max_bonus_score: {company.max_bonus_score} → {update_data.max_bonus_score}")
        company.max_bonus_score = update_data.max_bonus_score
    if update_data.is_active is not None:
        changes.append(f"is_active: {company.is_active} → {update_data.is_active}")
        company.is_active = update_data.is_active

    # 가산점 룰 업데이트 (전체 교체 방식)
    if update_data.bonus_rules is not None:
        db.query(BonusRule).filter(BonusRule.company_id == company_id).delete()
        for rule_data in update_data.bonus_rules:
            rule = BonusRule(
                company_id=company_id,
                category=rule_data.category,
                certificate_name=rule_data.certificate_name,
                grade=rule_data.grade,
                score=rule_data.score,
                calc_type=rule_data.calc_type,
                base_score=rule_data.base_score,
                series_filter=rule_data.series_filter,
            )
            db.add(rule)
        changes.append(f"bonus_rules 전체 교체 ({len(update_data.bonus_rules)}개)")

    company.updated_at = datetime.utcnow()

    # ADMIN_LOG 기록
    log = AdminLog(
        company_id=company_id,
        action="MANUAL_UPDATE",
        changed_by=current_admin,
        detail=" | ".join(changes) if changes else "변경 없음",
        created_at=datetime.utcnow(),
    )
    db.add(log)
    db.commit()
    db.refresh(company)

    logger.info(f"[Admin] 공기업 수정: ID={company_id}, 변경={changes} (by {current_admin})")
    return company


@router.post("/admin/sync", response_model=SyncResponse, summary="관리자: 외부 API DB 동기화")
async def admin_sync(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """
    관리자: 외부 API(잡알리오 등)에서 채용 공고 및 가산점 변경 사항을 동기화합니다.
    API 호출 실패 시 오류 로그만 기록하고 기존 DB를 유지합니다 (SRS 6.3).
    """
    try:
        result = await sync_from_external_api(db)
        log = AdminLog(
            company_id=None,
            action="AUTO_SYNC",
            changed_by=current_admin,
            detail=f"외부 API 동기화 완료: {result}",
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        logger.info(f"[Admin] 외부 API 동기화 성공 (by {current_admin}): {result}")
        return SyncResponse(status="success", message=f"동기화 완료: {result}")
    except Exception as e:
        # 외부 API 실패 → 오류 로그만 기록, 시스템 중단 없음 (SRS 6.3)
        log = AdminLog(
            company_id=None,
            action="AUTO_SYNC",
            changed_by=current_admin,
            detail=f"외부 API 동기화 실패: {str(e)}",
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        logger.error(f"[Admin] 외부 API 동기화 실패: {e}")
        return SyncResponse(
            status="error",
            message=f"외부 API 연동 실패 (기존 DB 유지): {str(e)}"
        )


@router.get("/admin/logs", response_model=List[AdminLogItem], summary="관리자: 변경 이력 조회")
async def admin_get_logs(
    db: Session = Depends(get_db),
    current_admin: str = Depends(get_current_admin),
):
    """관리자: ADMIN_LOG 조회 (최근 100건)"""
    logs = (
        db.query(AdminLog)
        .order_by(AdminLog.created_at.desc())
        .limit(100)
        .all()
    )
    return logs
