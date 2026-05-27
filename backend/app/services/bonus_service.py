"""비즈니스 로직 서비스 레이어 (DB ↔ 룰 엔진 중간 연결)"""
from sqlalchemy.orm import Session
from app.models.models import Company, BonusRule
from app.engine.rule_engine import CompanyRuleSet, BonusRuleItem


# ── 직렬 → series_filter 매핑 테이블 ──────────────────────────────────────
# 실제 공기업 자격증 DB (공기업 자격증.md)의 series_filter 값을 기반으로 구성.
# 사용자가 선택한 직렬에 따라 어떤 series_filter 값을 가진 룰을 적용할지 결정.
#
#  - "공통"은 모든 직렬에 항상 포함
#  - "사무·기술(ICT제외)" : ICT/IT 직군 제외한 사무·기술 직군에 공통 적용
#  - "공통(IT직군제외)"   : IT 직군 제외한 모든 직군에 공통 적용
#  - "기계·전기"          : 기계·전기 복합 직군 (기계, 전기 모두 해당)

SERIES_FILTER_MAP: dict[str, list[str]] = {
    # ── 일반 사무/행정직 ────────────────────────────────────────────────────
    # 한국수자원공사: '행정' / 한국중부발전: '사무'
    "행정": ["행정", "사무", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "사무": ["사무", "행정", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    # 한국수자원공사: '기술' (모든 기술직 포괄) / 한국중부발전: '기술'
    "기술": ["기술", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],

    # ── 전력·에너지 기술직 ─────────────────────────────────────────────────
    # 한국수자원공사의 '기술' 시리즈에 전기 규칙도 포함
    # 한국서부발전: '전기' / KORAIL: '전기통신' / 한국중부발전: '기계·전기'
    "전기":   ["전기", "기술", "공통", "기계·전기", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "기계":   ["기계", "기술", "공통", "기계·전기", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "화학":   ["화학", "기술", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    # KORAIL 전기통신직 = 전기+통신 포함
    "전기통신": ["전기통신", "전기", "기술", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],

    # ── IT 직군 (ICT제외 필터는 해당 없음) ────────────────────────────────
    "IT":  ["IT",  "기술", "공통"],
    "ICT": ["ICT", "IT", "기술", "공통"],

    # ── 건설·토목·건축 ────────────────────────────────────────────────────
    "토목": ["토목", "기술", "건설", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "건축": ["건축", "기술", "건설", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "건설": ["건설", "기술", "토목", "건축", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],

    # ── 철도 특수직 ────────────────────────────────────────────────────────
    "사무영업·열차승무": ["사무영업·열차승무", "사무영업", "공통"],
    "운전": ["운전", "공통"],
    "차량": ["차량", "공통"],

    # ── 하위 호환: 구(舊) 사무직/기술직 선택 지원 ──────────────────────
    "사무직": ["행정", "사무", "공통", "사무·기술(ICT제외)", "공통(IT직군제외)"],
    "기술직": [
        "기술", "전기", "기계", "화학", "토목", "건축",
        "전기통신", "건설", "기계·전기",
        "공통", "사무·기술(ICT제외)", "공통(IT직군제외)",
    ],
}


def get_series_filters(job_series: str) -> list[str]:
    """직렬명 → 매칭 series_filter 목록 반환 (폴백: ['공통', job_series])"""
    return SERIES_FILTER_MAP.get(job_series, ["공통", job_series])


def get_companies_with_rules(db: Session, job_series: str) -> list[CompanyRuleSet]:
    """
    선택 직렬에 맞는 전체 공기업 + 가산점 룰을 DB에서 조회.

    모든 공기업(series_type='공통')을 반환하되,
    각 기업의 룰은 선택 직렬에 해당하는 series_filter 값만 포함.
    """
    # 전체 활성 공기업 조회 (series_type 불문 — 실제 데이터는 모두 '공통')
    companies = (
        db.query(Company)
        .filter(Company.is_active == True)
        .all()
    )

    # 직렬에 해당하는 series_filter 목록
    filter_values = get_series_filters(job_series)

    result: list[CompanyRuleSet] = []
    for company in companies:
        rules = (
            db.query(BonusRule)
            .filter(
                BonusRule.company_id == company.id,
                BonusRule.series_filter.in_(filter_values),
                # PERCENT 룰은 필기 가산점 형태로 별도 운영 — 점수 계산에서 제외
                BonusRule.calc_type.in_(["FIXED", "PROPORTIONAL"]),
            )
            .all()
        )

        rule_items = [
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
            for r in rules
        ]

        result.append(
            CompanyRuleSet(
                company_id=company.id,
                company_name=company.name,
                max_bonus_score=company.max_bonus_score,
                rules=rule_items,
            )
        )

    return result
