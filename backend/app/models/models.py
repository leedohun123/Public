"""SQLAlchemy ORM 모델 정의 (PRD 4.1 ER Diagram 기반)"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.database import Base


class Company(Base):
    """공기업 기본 정보 테이블"""
    __tablename__ = "company"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, comment="공기업 명칭")
    series_type = Column(String(20), nullable=False, comment="적용 직렬: 사무직/기술직/공통")
    max_bonus_score = Column(Integer, nullable=False, comment="기업별 가산점 상한선")
    is_active = Column(Boolean, default=True, comment="채용 중단 기업 비활성화")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bonus_rules = relationship("BonusRule", back_populates="company", cascade="all, delete-orphan")
    admin_logs = relationship("AdminLog", back_populates="company")

    # Index for series_type filtering performance (SRS 6.1)
    __table_args__ = (
        Index("ix_company_series_type", "series_type"),
        Index("ix_company_is_active", "is_active"),
    )


class BonusRule(Base):
    """공기업별 가산점 룰 테이블 (OR 룰 단위: category 컬럼)"""
    __tablename__ = "bonus_rule"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    category = Column(String(50), nullable=False, comment="자격증 계열 (OR 룰 적용 단위: IT/어학/행정 등)")
    certificate_name = Column(String(100), nullable=False, comment="자격증 또는 어학 시험명")
    grade = Column(String(20), nullable=False, comment="급수 또는 등급 (1급, IH, 990 등)")
    score = Column(Float, nullable=False, comment="부여 가산점")
    calc_type = Column(String(20), nullable=False, default="FIXED", comment="FIXED 또는 PROPORTIONAL")
    base_score = Column(Integer, nullable=True, comment="PROPORTIONAL 방식의 만점 기준")
    series_filter = Column(String(20), default="공통", comment="해당 룰의 직렬 한정 여부")

    # Relationships
    company = relationship("Company", back_populates="bonus_rules")

    # Performance Index (SRS 6.1)
    __table_args__ = (
        Index("ix_bonus_rule_company_id", "company_id"),
        Index("ix_bonus_rule_category", "category"),
        Index("ix_bonus_rule_company_category", "company_id", "category"),
    )


class AdminLog(Base):
    """관리자 DB 변경 이력 테이블"""
    __tablename__ = "admin_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("company.id"), nullable=True)
    action = Column(String(30), nullable=False, comment="MANUAL_UPDATE / AUTO_SYNC")
    changed_by = Column(String(50), nullable=False, comment="관리자 식별자")
    detail = Column(Text, nullable=True, comment="변경 내용 요약")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    company = relationship("Company", back_populates="admin_logs")
