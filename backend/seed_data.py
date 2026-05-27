"""
샘플 공기업 가산점 DB 시드 데이터 삽입 스크립트
실제 공기업 가산점 정책을 참고하여 구성한 예시 데이터입니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.database import SessionLocal, engine
from app.models.models import Base, Company, BonusRule

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 이미 데이터가 있으면 스킵
    if db.query(Company).count() > 0:
        print("[OK] 시드 데이터가 이미 존재합니다. 스킵합니다.")
        db.close()
        return

    print("[SEED] 시드 데이터를 삽입합니다...")

    # ── 공기업 목록 ──────────────────────────────────────────────────────
    companies_data = [
        {"name": "한국전력공사", "series_type": "공통", "max_bonus_score": 20},
        {"name": "한국철도공사(KORAIL)", "series_type": "공통", "max_bonus_score": 20},
        {"name": "국민건강보험공단", "series_type": "사무직", "max_bonus_score": 20},
        {"name": "근로복지공단", "series_type": "사무직", "max_bonus_score": 15},
        {"name": "LH한국토지주택공사", "series_type": "공통", "max_bonus_score": 20},
        {"name": "한국수자원공사", "series_type": "공통", "max_bonus_score": 18},
        {"name": "한국도로공사", "series_type": "공통", "max_bonus_score": 20},
        {"name": "국민연금공단", "series_type": "사무직", "max_bonus_score": 20},
        {"name": "한국산업인력공단", "series_type": "사무직", "max_bonus_score": 15},
        {"name": "한국가스공사", "series_type": "기술직", "max_bonus_score": 20},
    ]

    companies = []
    for data in companies_data:
        c = Company(
            name=data["name"],
            series_type=data["series_type"],
            max_bonus_score=data["max_bonus_score"],
            is_active=True,
            updated_at=datetime.utcnow(),
        )
        db.add(c)
        companies.append(c)

    db.flush()  # ID 생성을 위해 flush

    # ── 가산점 룰 정의 ────────────────────────────────────────────────────
    # 공기업별 룰은 실제 공고 기반 예시입니다.
    # category가 같으면 OR 룰 적용 (동일 계열 중 최고 1개만 반영)

    def add_common_rules(company: Company, toeic_max_score: float = 5.0):
        """공통 자격증 룰 추가 (대부분 공기업에 적용)"""
        rules = [
            # IT 카테고리 (OR 룰 단위)
            BonusRule(company_id=company.id, category="IT", certificate_name="컴퓨터활용능력", grade="1급", score=5.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="IT", certificate_name="컴퓨터활용능력", grade="2급", score=3.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="IT", certificate_name="컴퓨터활용능력", grade="3급", score=1.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="IT", certificate_name="정보처리기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="IT", certificate_name="정보처리산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="IT", certificate_name="워드프로세서", grade="1급", score=2.0, calc_type="FIXED", series_filter="공통"),
            # 역사 카테고리 (OR 룰 단위)
            BonusRule(company_id=company.id, category="역사", certificate_name="한국사능력검정시험", grade="1급", score=5.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="역사", certificate_name="한국사능력검정시험", grade="2급", score=4.0, calc_type="FIXED", series_filter="공통"),
            BonusRule(company_id=company.id, category="역사", certificate_name="한국사능력검정시험", grade="3급", score=2.0, calc_type="FIXED", series_filter="공통"),
            # 어학 카테고리 (PROPORTIONAL 방식)
            BonusRule(company_id=company.id, category="어학", certificate_name="TOEIC", grade="990", score=toeic_max_score, calc_type="PROPORTIONAL", base_score=990, series_filter="공통"),
            BonusRule(company_id=company.id, category="어학", certificate_name="토익스피킹", grade="Lv.6", score=toeic_max_score, calc_type="FIXED", base_score=None, series_filter="공통"),
            BonusRule(company_id=company.id, category="어학", certificate_name="OPIc", grade="IH", score=toeic_max_score, calc_type="FIXED", base_score=None, series_filter="공통"),
        ]
        for r in rules:
            db.add(r)

    # 1. 한국전력공사 (공통, max 20)
    kepco = companies[0]
    add_common_rules(kepco, toeic_max_score=5.0)
    db.add_all([
        # 경영/행정 자격증 (사무직 전용)
        BonusRule(company_id=kepco.id, category="경영", certificate_name="경영지도사", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=kepco.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        # 전기 자격증 (기술직 전용)
        BonusRule(company_id=kepco.id, category="전기", certificate_name="전기기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kepco.id, category="전기", certificate_name="전기산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="기술직"),
    ])

    # 2. 한국철도공사 (공통, max 20)
    korail = companies[1]
    add_common_rules(korail, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=korail.id, category="경영", certificate_name="경영지도사", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=korail.id, category="기계", certificate_name="일반기계기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=korail.id, category="기계", certificate_name="기계설비기사", grade="1급", score=4.0, calc_type="FIXED", series_filter="기술직"),
    ])

    # 3. 국민건강보험공단 (사무직, max 20)
    nhis = companies[2]
    add_common_rules(nhis, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=nhis.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nhis.id, category="경영", certificate_name="세무사", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nhis.id, category="경영", certificate_name="사회조사분석사", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nhis.id, category="경영", certificate_name="사회조사분석사", grade="2급", score=2.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 4. 근로복지공단 (사무직, max 15)
    kwc = companies[3]
    add_common_rules(kwc, toeic_max_score=3.0)
    db.add_all([
        BonusRule(company_id=kwc.id, category="경영", certificate_name="공인노무사", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=kwc.id, category="경영", certificate_name="세무사", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 5. LH한국토지주택공사 (공통, max 20)
    lh = companies[4]
    add_common_rules(lh, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=lh.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=lh.id, category="건축", certificate_name="건축기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=lh.id, category="건축", certificate_name="건축산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=lh.id, category="토목", certificate_name="토목기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=lh.id, category="토목", certificate_name="토목산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="기술직"),
    ])

    # 6. 한국수자원공사 (공통, max 18)
    kwrc = companies[5]
    add_common_rules(kwrc, toeic_max_score=4.0)
    db.add_all([
        BonusRule(company_id=kwrc.id, category="토목", certificate_name="토목기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kwrc.id, category="토목", certificate_name="토목산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kwrc.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 7. 한국도로공사 (공통, max 20)
    ex = companies[6]
    add_common_rules(ex, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=ex.id, category="토목", certificate_name="토목기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=ex.id, category="전기", certificate_name="전기기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=ex.id, category="경영", certificate_name="경영지도사", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=ex.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 8. 국민연금공단 (사무직, max 20)
    nps = companies[7]
    add_common_rules(nps, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=nps.id, category="경영", certificate_name="공인회계사(CPA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nps.id, category="경영", certificate_name="금융투자분석사(CFA)", grade="1급", score=5.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nps.id, category="경영", certificate_name="세무사", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=nps.id, category="경영", certificate_name="사회조사분석사", grade="1급", score=3.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 9. 한국산업인력공단 (사무직, max 15)
    hrdk = companies[8]
    add_common_rules(hrdk, toeic_max_score=3.0)
    db.add_all([
        BonusRule(company_id=hrdk.id, category="경영", certificate_name="경영지도사", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
        BonusRule(company_id=hrdk.id, category="경영", certificate_name="공인노무사", grade="1급", score=4.0, calc_type="FIXED", series_filter="사무직"),
    ])

    # 10. 한국가스공사 (기술직, max 20)
    kogas = companies[9]
    add_common_rules(kogas, toeic_max_score=5.0)
    db.add_all([
        BonusRule(company_id=kogas.id, category="가스", certificate_name="가스기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kogas.id, category="가스", certificate_name="가스산업기사", grade="2급", score=3.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kogas.id, category="전기", certificate_name="전기기사", grade="1급", score=5.0, calc_type="FIXED", series_filter="기술직"),
        BonusRule(company_id=kogas.id, category="기계", certificate_name="일반기계기사", grade="1급", score=4.0, calc_type="FIXED", series_filter="기술직"),
    ])

    db.commit()
    print(f"[OK] 시드 데이터 삽입 완료: 공기업 {len(companies_data)}개, 가산점 룰 다수")
    db.close()


if __name__ == "__main__":
    seed()
