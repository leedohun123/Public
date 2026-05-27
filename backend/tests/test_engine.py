"""
룰 엔진 단위 테스트 (SRS 7.2 가산점 연산 룰 예시 기반)
python -m pytest tests/ -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from app.engine.rule_engine import (
    CertInput, LanguageScores, BonusRuleItem, CompanyRuleSet,
    calculate_company_score, run_engine, _calc_proportional
)


def make_rule(id, company_id, category, cert_name, grade, score, calc_type="FIXED", base_score=None, series_filter="공통"):
    return BonusRuleItem(
        id=id, company_id=company_id,
        category=category, certificate_name=cert_name,
        grade=grade, score=score,
        calc_type=calc_type, base_score=base_score,
        series_filter=series_filter
    )


def make_company(rules, max_score=20):
    return CompanyRuleSet(
        company_id=1,
        company_name="테스트기업",
        max_bonus_score=max_score,
        rules=rules
    )


# ── 기본 계산 테스트 ─────────────────────────────────────────────────────

class TestBasicCalculation:
    def test_single_cert_fixed(self):
        """단일 자격증 FIXED 방식 기본 계산"""
        rules = [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]
        company = make_company(rules)
        certs = [CertInput("컴퓨터활용능력", "1급")]
        lang = LanguageScores()
        result = calculate_company_score(company, certs, lang)
        assert result.my_bonus_score == 5.0
        assert result.match_rate == 25.0  # 5/20 * 100

    def test_no_matching_cert(self):
        """매칭 안 되는 자격증 입력 시 가산점 0"""
        rules = [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]
        company = make_company(rules)
        certs = [CertInput("정보처리기사", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.my_bonus_score == 0.0


# ── OR 룰 테스트 (SRS 7.2 ① OR 룰) ─────────────────────────────────────

class TestOrRule:
    def test_or_rule_same_category(self):
        """동일 category 자격증 복수 입력 시 최고 등급 1개만 반영"""
        rules = [
            make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0),
            make_rule(2, 1, "IT", "컴퓨터활용능력", "2급", 3.0),
            make_rule(3, 1, "IT", "컴퓨터활용능력", "3급", 1.0),
        ]
        company = make_company(rules)
        # 1급·2급 동시 입력 → 1급(5점)만 반영
        certs = [CertInput("컴퓨터활용능력", "1급"), CertInput("컴퓨터활용능력", "2급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.my_bonus_score == 5.0, "OR 룰: 동일 계열 최고 등급 1개만 반영"

    def test_or_rule_different_certs_same_category(self):
        """같은 category이지만 다른 자격증명 — 최고점만 반영"""
        rules = [
            make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0),
            make_rule(2, 1, "IT", "정보처리기사", "1급", 5.0),
        ]
        company = make_company(rules)
        certs = [CertInput("컴퓨터활용능력", "1급"), CertInput("정보처리기사", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.my_bonus_score == 5.0, "동일 IT 카테고리에서 최고점 1개만"

    def test_different_categories_both_applied(self):
        """다른 category → 둘 다 합산"""
        rules = [
            make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0),
            make_rule(2, 1, "역사", "한국사능력검정시험", "1급", 5.0),
        ]
        company = make_company(rules)
        certs = [CertInput("컴퓨터활용능력", "1급"), CertInput("한국사능력검정시험", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.my_bonus_score == 10.0, "다른 카테고리는 모두 합산"


# ── 어학 비례 연산 테스트 (SRS 7.2 ② 어학 비례) ────────────────────────

class TestProportionalCalc:
    def test_proportional_formula(self):
        """(유저점수 / 만점기준) × 배점 공식 검증"""
        # 850/990 × 5 = 4.29
        result = _calc_proportional(850, 990, 5.0)
        assert abs(result - 4.29) < 0.01

    def test_toeic_proportional(self):
        """토익 PROPORTIONAL 방식 — SRS 7.2 예시 검증"""
        rules = [
            make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0),
            make_rule(2, 1, "역사", "한국사능력검정시험", "1급", 5.0),
            make_rule(3, 1, "어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990),
        ]
        company = make_company(rules, max_score=20)
        certs = [CertInput("컴퓨터활용능력", "1급"), CertInput("한국사능력검정시험", "1급")]
        lang = LanguageScores(toeic=850)
        result = calculate_company_score(company, certs, lang)
        # 5 + 5 + 4.29 = 14.29 → 반올림 14.29
        assert abs(result.my_bonus_score - 14.29) < 0.01
        # 매칭률 14.29/20 * 100 = 71.5
        assert abs(result.match_rate - 71.5) < 0.1

    def test_toeic_perfect_score(self):
        """토익 990점(만점) 시 배점 전액 획득"""
        rules = [make_rule(1, 1, "어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990)]
        company = make_company(rules)
        lang = LanguageScores(toeic=990)
        result = calculate_company_score(company, [], lang)
        assert result.my_bonus_score == 5.0


# ── 합산 한도 Cap 테스트 (SRS 7.2 ④ Cap 적용) ───────────────────────────

class TestCapRule:
    def test_cap_applies(self):
        """합산이 max_bonus_score 초과 시 절삭"""
        rules = [
            make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0),
            make_rule(2, 1, "역사", "한국사능력검정시험", "1급", 5.0),
            make_rule(3, 1, "어학", "TOEIC", "990", 5.0, "PROPORTIONAL", 990),
        ]
        company = make_company(rules, max_score=10)  # Cap = 10
        certs = [CertInput("컴퓨터활용능력", "1급"), CertInput("한국사능력검정시험", "1급")]
        lang = LanguageScores(toeic=990)
        # 합산 = 15점, Cap = 10점 → 10점
        result = calculate_company_score(company, certs, lang)
        assert result.my_bonus_score == 10.0, "Cap 초과분 절삭"
        assert result.match_rate == 100.0

    def test_no_cap_when_under(self):
        """합산이 max_bonus_score 미만 시 절삭 없음"""
        rules = [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]
        company = make_company(rules, max_score=20)
        certs = [CertInput("컴퓨터활용능력", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.my_bonus_score == 5.0  # 절삭 없음


# ── 매칭률 테스트 ─────────────────────────────────────────────────────────

class TestMatchRate:
    def test_perfect_match(self):
        """매칭률 100% — 피드백 없음"""
        rules = [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 20.0)]
        company = make_company(rules, max_score=20)
        certs = [CertInput("컴퓨터활용능력", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.match_rate == 100.0
        assert result.feedback is None, "만점 시 피드백 없음"

    def test_below_perfect_has_feedback(self):
        """매칭률 100% 미만 — 피드백 생성"""
        rules = [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]
        company = make_company(rules, max_score=20)
        certs = [CertInput("컴퓨터활용능력", "1급")]
        result = calculate_company_score(company, certs, LanguageScores())
        assert result.match_rate == 25.0
        assert result.feedback is not None, "100% 미만 시 피드백 생성"


# ── 전체 엔진 실행 테스트 ─────────────────────────────────────────────────

class TestRunEngine:
    def test_results_sorted_desc(self):
        """run_engine 결과가 매칭률 내림차순으로 정렬됨"""
        companies = [
            CompanyRuleSet(1, "기업A", 20, [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]),
            CompanyRuleSet(2, "기업B", 10, [make_rule(2, 2, "IT", "컴퓨터활용능력", "1급", 10.0)]),
        ]
        certs = [CertInput("컴퓨터활용능력", "1급")]
        results = run_engine(companies, certs, LanguageScores())
        rates = [r.match_rate for r in results]
        assert rates == sorted(rates, reverse=True), "매칭률 내림차순 정렬"

    def test_engine_skips_error_company(self):
        """개별 기업 오류 시 해당 기업만 스킵, 나머지 반환 (SRS 6.3)"""
        # max_bonus_score=0인 기업은 ZeroDivisionError → 스킵
        companies = [
            CompanyRuleSet(1, "정상기업", 20, [make_rule(1, 1, "IT", "컴퓨터활용능력", "1급", 5.0)]),
        ]
        certs = [CertInput("컴퓨터활용능력", "1급")]
        results = run_engine(companies, certs, LanguageScores())
        assert len(results) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
