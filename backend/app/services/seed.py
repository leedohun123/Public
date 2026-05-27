"""
초기 시드 데이터 삽입 (DB가 비어있을 때만 실행)
공기업 가산점 규정 기반 데이터 (2025~2026년 기준)
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Company, BonusRule

logger = logging.getLogger(__name__)


# ── 시드 데이터 정의 ─────────────────────────────────────────────────────
# 구조: (company_name, series_type, max_bonus_score, rules[])
# rule: (category, certificate_name, grade, score, calc_type, base_score, series_filter)

SEED_DATA = [
    {
        "name": "한국전력공사",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            # IT 자격증 (OR 룰)
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("IT", "정보처리산업기사", "산업기사", 3.0, "FIXED", None, "공통"),
            # 한국사 (OR 룰)
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "3급", 1.0, "FIXED", None, "공통"),
            # 어학 (비례)
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            # 경영/회계
            ("경영회계", "공인회계사", "기술사급", 5.0, "FIXED", None, "공통"),
            ("경영회계", "공인회계사", "기사급", 3.0, "FIXED", None, "공통"),
        ],
    },
    {
        "name": "한국철도공사(KORAIL)",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인노무사", "기술사급", 5.0, "FIXED", None, "공통"),
        ],
    },
    {
        "name": "국민건강보험공단",
        "series_type": "사무직",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인회계사", "기술사급", 5.0, "FIXED", None, "사무직"),
            ("경영회계", "공인회계사", "기사급", 3.0, "FIXED", None, "사무직"),
        ],
    },
    {
        "name": "근로복지공단",
        "series_type": "사무직",
        "max_bonus_score": 15,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 4.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 2.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 4.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 4.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 2.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 4.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인노무사", "기술사급", 3.0, "FIXED", None, "사무직"),
            ("경영회계", "공인노무사", "기사급", 2.0, "FIXED", None, "사무직"),
        ],
    },
    {
        "name": "LH한국토지주택공사",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            # 토목/건설 기술직 전용
            ("토목건설", "토목기사", "기사", 5.0, "FIXED", None, "기술직"),
            ("토목건설", "건축기사", "기사", 5.0, "FIXED", None, "기술직"),
        ],
    },
    {
        "name": "국민연금공단",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인회계사", "기술사급", 5.0, "FIXED", None, "사무직"),
            ("경영회계", "세무사", "기술사급", 3.0, "FIXED", None, "사무직"),
        ],
    },
    {
        "name": "한국수력원자력",
        "series_type": "기술직",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 3.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 3.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 2.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 4.0, "PROPORTIONAL", 990, "공통"),
            # 전기 계열
            ("전기", "전기기사", "기사", 7.0, "FIXED", None, "기술직"),
            ("전기", "전기산업기사", "산업기사", 5.0, "FIXED", None, "기술직"),
            ("전기", "전기기능장", "기능장", 7.0, "FIXED", None, "기술직"),
            # 원자력 계열
            ("원자력", "원자력기사", "기사", 7.0, "FIXED", None, "기술직"),
        ],
    },
    {
        "name": "한국가스공사",
        "series_type": "기술직",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 3.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 4.0, "PROPORTIONAL", 990, "공통"),
            # 가스/기계 계열
            ("가스기계", "가스기사", "기사", 7.0, "FIXED", None, "기술직"),
            ("가스기계", "가스산업기사", "산업기사", 5.0, "FIXED", None, "기술직"),
            ("가스기계", "일반기계기사", "기사", 5.0, "FIXED", None, "기술직"),
            ("화학환경", "화공기사", "기사", 5.0, "FIXED", None, "기술직"),
        ],
    },
    {
        "name": "한국도로공사",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 3.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("토목건설", "토목기사", "기사", 5.0, "FIXED", None, "기술직"),
            ("토목건설", "토목산업기사", "산업기사", 3.0, "FIXED", None, "기술직"),
        ],
    },
    {
        "name": "한국수자원공사",
        "series_type": "공통",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 3.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("토목건설", "토목기사", "기사", 5.0, "FIXED", None, "기술직"),
            ("화학환경", "수질환경기사", "기사", 5.0, "FIXED", None, "기술직"),
        ],
    },
    {
        "name": "건강보험심사평가원",
        "series_type": "사무직",
        "max_bonus_score": 15,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 4.0, "FIXED", None, "공통"),
            ("IT", "컴퓨터활용능력", "2급", 2.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 4.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 4.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "2급", 2.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 4.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인회계사", "기술사급", 3.0, "FIXED", None, "사무직"),
        ],
    },
    {
        "name": "한국산업은행",
        "series_type": "사무직",
        "max_bonus_score": 20,
        "rules": [
            ("IT", "컴퓨터활용능력", "1급", 5.0, "FIXED", None, "공통"),
            ("IT", "정보처리기사", "기사", 5.0, "FIXED", None, "공통"),
            ("역사", "한국사능력검정시험", "1급", 5.0, "FIXED", None, "공통"),
            ("어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990, "공통"),
            ("경영회계", "공인회계사", "기술사급", 5.0, "FIXED", None, "사무직"),
            ("경영회계", "세무사", "기술사급", 5.0, "FIXED", None, "사무직"),
            ("경영회계", "변호사", "기술사급", 5.0, "FIXED", None, "사무직"),
        ],
    },
]


def seed_initial_data(db: Session) -> None:
    """DB가 비어있을 때만 시드 데이터 삽입"""
    if db.query(Company).count() > 0:
        logger.info("시드 데이터 이미 존재 — 스킵")
        return

    logger.info("시드 데이터 삽입 시작...")
    for company_data in SEED_DATA:
        company = Company(
            name=company_data["name"],
            series_type=company_data["series_type"],
            max_bonus_score=company_data["max_bonus_score"],
            is_active=True,
            updated_at=datetime.utcnow(),
        )
        db.add(company)
        db.flush()  # company.id 확보

        for rule_tuple in company_data["rules"]:
            category, cert_name, grade, score, calc_type, base_score, series_filter = rule_tuple
            rule = BonusRule(
                company_id=company.id,
                category=category,
                certificate_name=cert_name,
                grade=grade,
                score=score,
                calc_type=calc_type,
                base_score=base_score,
                series_filter=series_filter,
            )
            db.add(rule)

    db.commit()
    logger.info(f"시드 데이터 삽입 완료: {len(SEED_DATA)}개 공기업")
