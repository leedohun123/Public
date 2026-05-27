"""
가산점 연산 룰 엔진 (PRD REQ-004, SRS UC-004)
독립 모듈로 분리하여 다른 기능과의 결합도 최소화 (SRS 6.4 유지보수성)

지원 룰:
  1. OR 룰: 동일 category 자격증 중 최고 등급(score) 1개만 반영
  2. PROPORTIONAL 어학 비례 연산: (유저 점수 / base_score) × score
  3. 합산 한도(Cap) 룰: max_bonus_score 초과분 절삭
  4. 매칭률 계산: (내 가산점 / max_bonus_score) × 100
  5. 피드백 멘트 생성: 100% 미만 기업 대상
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CertInput:
    """사용자가 입력한 자격증 항목"""
    name: str        # 자격증 이름 (예: 컴퓨터활용능력)
    grade: str       # 급수 (예: 1급)


@dataclass
class LanguageScores:
    """사용자가 입력한 어학 성적"""
    toeic: Optional[int] = None          # 0~990
    toeic_speaking: Optional[str] = None  # Lv.1~Lv.8
    opic: Optional[str] = None           # NL/IL/IM1/IM2/IM3/IH/AL


@dataclass
class BonusRuleItem:
    """DB에서 로드한 가산점 룰 한 행"""
    id: int
    company_id: int
    category: str
    certificate_name: str
    grade: str
    score: float
    calc_type: str       # FIXED | PROPORTIONAL
    base_score: Optional[int]
    series_filter: str


@dataclass
class CompanyRuleSet:
    """기업별 가산점 룰 묶음"""
    company_id: int
    company_name: str
    max_bonus_score: int
    rules: list[BonusRuleItem] = field(default_factory=list)


@dataclass
class EngineResult:
    """기업별 연산 결과"""
    company_id: int
    company_name: str
    my_bonus_score: float
    max_bonus_score: int
    match_rate: float
    feedback: Optional[str]


# ── 어학 등급 → 점수 매핑 테이블 ──────────────────────────────────────────

# 토익스피킹 레벨 순서 (높을수록 좋음)
TOEIC_SPEAKING_ORDER = ["Lv.1", "Lv.2", "Lv.3", "Lv.4", "Lv.5", "Lv.6", "Lv.7", "Lv.8"]

# OPIc 등급 순서 (높을수록 좋음)
OPIC_ORDER = ["NL", "IL", "IM1", "IM2", "IM3", "IH", "AL"]

# 자격증 급수 순서 (높을수록 좋음 — grade 비교에서 숫자 기반)
# 숫자가 작을수록 높은 급수: 1급 > 2급 > 3급
# 별도 로직으로 처리


def _grade_to_sort_key(grade: str) -> float:
    """
    자격증 급수/등급을 비교 가능한 숫자로 변환.
    낮은 숫자 = 더 높은 등급.
    """
    grade = grade.strip()
    # 숫자 급수 처리: "1급" → 1, "2급" → 2
    if grade.endswith("급"):
        try:
            return float(grade.replace("급", "").strip())
        except ValueError:
            pass
    # 등급 숫자 처리: "1등급" → 1
    if grade.endswith("등급"):
        try:
            return float(grade.replace("등급", "").strip())
        except ValueError:
            pass
    # 기타 → 0 (최고로 취급)
    return 0.0


def _toeic_speaking_to_numeric(level: str) -> int:
    """토익스피킹 레벨을 숫자로 변환"""
    try:
        return TOEIC_SPEAKING_ORDER.index(level)
    except ValueError:
        return -1


def _opic_to_numeric(grade: str) -> int:
    """OPIc 등급을 숫자로 변환"""
    try:
        return OPIC_ORDER.index(grade)
    except ValueError:
        return -1


def _calc_proportional(user_score: float, base_score: int, rule_score: float) -> float:
    """
    어학 비례 연산: (유저점수 / 만점기준) × 배점
    PRD REQ-004 / SRS 7.2 예시 기반
    """
    if base_score <= 0:
        return 0.0
    result = (user_score / base_score) * rule_score
    return round(result, 2)


def _match_language_rule(rule: BonusRuleItem, lang: LanguageScores) -> Optional[float]:
    """
    어학 룰과 사용자 어학 성적을 매칭하여 가산점 계산.
    매칭 안 되면 None 반환.
    """
    cert_name_lower = rule.certificate_name.upper().replace(" ", "")

    # TOEIC (토익) — PROPORTIONAL 방식
    if "TOEIC" in cert_name_lower and "SPEAKING" not in cert_name_lower and "스피킹" not in cert_name_lower:
        if lang.toeic is not None and lang.toeic > 0:
            if rule.calc_type == "PROPORTIONAL" and rule.base_score:
                return _calc_proportional(lang.toeic, rule.base_score, rule.score)
            else:
                # FIXED: 특정 점수 이상이면 고정 가산점
                try:
                    threshold = int(rule.grade.replace("점", "").replace("이상", "").strip())
                    if lang.toeic >= threshold:
                        return rule.score
                except (ValueError, AttributeError):
                    pass
        return None

    # 토익스피킹 (TOEIC Speaking)
    if "SPEAKING" in cert_name_lower or "스피킹" in cert_name_lower or "TOEIS" in cert_name_lower:
        if lang.toeic_speaking:
            user_level = _toeic_speaking_to_numeric(lang.toeic_speaking)
            rule_level = _toeic_speaking_to_numeric(rule.grade)
            if rule_level >= 0 and user_level >= rule_level:
                if rule.calc_type == "PROPORTIONAL" and rule.base_score:
                    return _calc_proportional(user_level + 1, rule.base_score, rule.score)
                return rule.score
        return None

    # OPIc
    if "OPIC" in cert_name_lower or "오픽" in cert_name_lower:
        if lang.opic:
            user_level = _opic_to_numeric(lang.opic)
            rule_level = _opic_to_numeric(rule.grade)
            if rule_level >= 0 and user_level >= rule_level:
                if rule.calc_type == "PROPORTIONAL" and rule.base_score:
                    return _calc_proportional(user_level + 1, rule.base_score, rule.score)
                return rule.score
        return None

    return None


def _is_language_rule(rule: BonusRuleItem) -> bool:
    """해당 룰이 어학 관련 룰인지 판단"""
    lang_keywords = ["TOEIC", "토익", "OPIC", "오픽", "SPEAKING", "스피킹", "어학"]
    cert_upper = rule.certificate_name.upper()
    return any(kw.upper() in cert_upper for kw in lang_keywords)


def calculate_company_score(
    company: CompanyRuleSet,
    certificates: list[CertInput],
    language_scores: LanguageScores,
) -> EngineResult:
    """
    단일 기업에 대한 가산점 계산 (SRS 3.2 시퀀스 다이어그램 기반)

    Steps:
      1. OR 룰: 동일 category 내 최고 score 룰 1개만 반영
      2. 어학 비례 연산 / 어학 FIXED 룰 처리
      3. 합산 한도(Cap) 적용
      4. 매칭률 계산
      5. 피드백 생성
    """
    rules = company.rules
    total_score = 0.0

    # 자격증명 → 입력 세트 (대소문자 무시)
    cert_input_set = {(c.name.strip(), c.grade.strip()) for c in certificates}
    cert_name_set = {c.name.strip() for c in certificates}

    # ── STEP 1: 자격증 룰 처리 (OR 룰 포함) ─────────────────────────────
    # category 별로 룰을 그룹화
    cert_rules_by_category: dict[str, list[BonusRuleItem]] = {}
    lang_rules: list[BonusRuleItem] = []

    for rule in rules:
        if _is_language_rule(rule):
            lang_rules.append(rule)
        else:
            cert_rules_by_category.setdefault(rule.category, []).append(rule)

    # OR 룰: 카테고리별로 사용자가 가진 자격증 중 가장 높은 가산점 1개만 선택
    matched_cert_scores: list[float] = []
    for category, cat_rules in cert_rules_by_category.items():
        best_score: Optional[float] = None
        for rule in cat_rules:
            # 사용자 입력 자격증과 매칭
            for cert in certificates:
                name_match = rule.certificate_name.strip() == cert.name.strip()
                grade_match = rule.grade.strip() == cert.grade.strip()
                if name_match and grade_match:
                    if best_score is None or rule.score > best_score:
                        best_score = rule.score
        if best_score is not None:
            matched_cert_scores.append(best_score)

    total_score += sum(matched_cert_scores)

    # ── STEP 2: 어학 룰 처리 ─────────────────────────────────────────────
    # 어학도 category 별 OR 룰 적용 (같은 category 내 최고 1개)
    lang_by_category: dict[str, list[BonusRuleItem]] = {}
    for rule in lang_rules:
        lang_by_category.setdefault(rule.category, []).append(rule)

    for category, l_rules in lang_by_category.items():
        best_lang_score: Optional[float] = None
        for rule in l_rules:
            score = _match_language_rule(rule, language_scores)
            if score is not None:
                if best_lang_score is None or score > best_lang_score:
                    best_lang_score = score
        if best_lang_score is not None:
            total_score += best_lang_score

    # ── STEP 3: 합산 한도(Cap) 적용 ─────────────────────────────────────
    my_bonus_score = min(round(total_score, 2), company.max_bonus_score)

    # ── STEP 4: 매칭률 계산 ──────────────────────────────────────────────
    if company.max_bonus_score > 0:
        match_rate = round((my_bonus_score / company.max_bonus_score) * 100, 1)
    else:
        match_rate = 0.0

    # ── STEP 5: 피드백 생성 ──────────────────────────────────────────────
    feedback = None
    if match_rate < 100.0:
        feedback = _generate_feedback(
            company=company,
            certificates=certificates,
            language_scores=language_scores,
            my_score=my_bonus_score,
        )

    return EngineResult(
        company_id=company.company_id,
        company_name=company.company_name,
        my_bonus_score=my_bonus_score,
        max_bonus_score=company.max_bonus_score,
        match_rate=match_rate,
        feedback=feedback,
    )


def _generate_feedback(
    company: CompanyRuleSet,
    certificates: list[CertInput],
    language_scores: LanguageScores,
    my_score: float,
) -> str:
    """
    스펙 보완 피드백 멘트 생성 (PRD REQ-006)
    부족한 항목을 분석하여 개인 맞춤형 가이드 제공
    """
    shortage = company.max_bonus_score - my_score
    tips = []

    cert_name_grade_set = {(c.name.strip(), c.grade.strip()) for c in certificates}
    cert_name_set = {c.name.strip() for c in certificates}

    # 카테고리별 best 가능 점수 vs 현재 획득 점수
    cert_rules_by_category: dict[str, list[BonusRuleItem]] = {}
    lang_rules: list[BonusRuleItem] = []

    for rule in company.rules:
        if _is_language_rule(rule):
            lang_rules.append(rule)
        else:
            cert_rules_by_category.setdefault(rule.category, []).append(rule)

    # 자격증 피드백: 미보유 항목 중 가장 높은 가산점 항목 추천
    for category, cat_rules in cert_rules_by_category.items():
        # 현재 이 카테고리에서 획득한 점수
        current_best = 0.0
        for rule in cat_rules:
            for cert in certificates:
                if rule.certificate_name.strip() == cert.name.strip() and rule.grade.strip() == cert.grade.strip():
                    if rule.score > current_best:
                        current_best = rule.score

        # 이 카테고리에서 가능한 최대 점수
        possible_max = max((r.score for r in cat_rules), default=0.0)
        gain = possible_max - current_best

        if gain > 0:
            best_rule = max(cat_rules, key=lambda r: r.score)
            tips.append(
                f"'{best_rule.certificate_name}({best_rule.grade})' 취득 시 +{gain:.1f}점 추가 가능"
            )

    # 어학 피드백
    if lang_rules:
        # 토익 PROPORTIONAL 룰 찾기
        toeic_prop_rule = next(
            (r for r in lang_rules
             if "TOEIC" in r.certificate_name.upper()
             and "SPEAKING" not in r.certificate_name.upper()
             and r.calc_type == "PROPORTIONAL"),
            None
        )
        if toeic_prop_rule and toeic_prop_rule.base_score:
            current_toeic = language_scores.toeic or 0
            max_lang_score = toeic_prop_rule.score
            current_lang_score = _calc_proportional(current_toeic, toeic_prop_rule.base_score, max_lang_score)
            if current_lang_score < max_lang_score:
                gain = round(max_lang_score - current_lang_score, 1)
                tips.append(
                    f"토익 {toeic_prop_rule.base_score}점 달성 시 어학 가산점 +{gain}점 추가 가능"
                )

    if not tips:
        tips.append(f"{company.company_name} 만점까지 {shortage:.1f}점 부족합니다.")

    # 최대 2개 팁만 노출
    feedback_text = " / ".join(tips[:2])
    feedback_text += f" (부족: {shortage:.1f}점)"
    return feedback_text


def run_engine(
    companies: list[CompanyRuleSet],
    certificates: list[CertInput],
    language_scores: LanguageScores,
) -> list[EngineResult]:
    """
    전체 기업 목록에 대해 가산점 계산 실행 후 매칭률 내림차순 정렬 반환.
    개별 기업 계산 오류 시 해당 기업만 스킵 (SRS 6.3 신뢰성)
    """
    results: list[EngineResult] = []

    for company in companies:
        try:
            result = calculate_company_score(company, certificates, language_scores)
            results.append(result)
        except Exception as e:
            # 개별 기업 오류 → 스킵 후 로그만 남김 (시스템 중단 방지)
            import logging
            logging.getLogger(__name__).error(
                f"[RuleEngine] 기업 ID={company.company_id} 계산 오류: {e}"
            )

    # 매칭률 내림차순 정렬
    results.sort(key=lambda r: r.match_rate, reverse=True)
    return results
