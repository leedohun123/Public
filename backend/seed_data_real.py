"""
실제 공기업 가산점 DB 시드 데이터
출처: 공기업 자격증.md (2026년 각 기관 실제 공채 공고 기준)

사용법:
  python seed_data_real.py          # 직접 실행
  from seed_data_real import seed_real; seed_real()  # 임포트
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from app.database import SessionLocal, engine
from app.models.models import Base, Company, BonusRule

# 원본 MD 파일 경로 (여러 위치 시도)
MD_FILE_CANDIDATES = [
    os.path.join(os.path.expanduser("~"), "OneDrive", "바탕 화면", "공기업 자격증.md"),
    r"C:\Users\leedh\OneDrive\바탕 화면\공기업 자격증.md",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "공기업 자격증.md"),
]

# company_id=1~11 에 대응하는 공기업 정보 (파일 순서와 동일)
COMPANY_LIST = [
    # (file_id, name,              series_type, max_bonus_score, updated_at)
    (1,  "한국수자원공사",            "공통", 20,  "2026-04-24"),
    (2,  "한국철도공사",              "공통", 20,  "2026-03-06"),
    (3,  "한국조폐공사",              "공통", 10,  "2026-05-27"),
    (4,  "국가철도공단",              "공통",  5,  "2026-05-27"),
    (5,  "국방과학연구소",            "공통", 20,  "2026-05-27"),
    (6,  "한국가스기술공사",          "공통", 60,  "2026-05-27"),
    (7,  "한국특허정보원",            "공통", 60,  "2026-05-27"),
    (8,  "중소기업기술정보진흥원",    "공통", 15,  "2026-05-27"),
    (9,  "한국서부발전",              "공통", 30,  "2026-05-27"),
    (10, "한국중부발전",              "공통", 40,  "2026-05-27"),
    (11, "건축공간연구원",            "공통", 10,  "2026-05-27"),
]

# BONUS_RULE 튜플 파싱 정규식
# (company_id, 'category', 'cert_name', 'grade', score, 'calc_type', NULL|base_score, 'series_filter')
BONUS_RULE_RE = re.compile(
    r"\(\s*(\d+)\s*,"           # group 1: company_id (정수)
    r"\s*'([^']*)'"             # group 2: category
    r"\s*,\s*'([^']*)'"         # group 3: certificate_name
    r"\s*,\s*'([^']*)'"         # group 4: grade
    r"\s*,\s*(\d+(?:\.\d+)?)"   # group 5: score (숫자)
    r"\s*,\s*'([^']*)'"         # group 6: calc_type
    r"\s*,\s*(NULL|\d+(?:\.\d+)?)"  # group 7: base_score (NULL 또는 숫자)
    r"\s*,\s*'([^']*)'"         # group 8: series_filter
    r"\s*\)"
)


def find_md_file() -> str | None:
    """공기업 자격증.md 파일 위치 탐색"""
    for path in MD_FILE_CANDIDATES:
        if os.path.exists(path):
            return path
    return None


def clean_md(content: str) -> str:
    """마크다운 이스케이프 문자 정리"""
    content = content.replace("&#x20;", " ")
    content = content.replace("\\_", "_")
    content = re.sub(r"\\--", "--", content)
    content = content.replace("\\[", "[").replace("\\]", "]")
    # 남은 백슬래시 이스케이프 제거
    content = re.sub(r"\\(.)", r"\1", content)
    return content


def parse_bonus_rules(md_path: str) -> list[tuple]:
    """
    MD 파일에서 BONUS_RULE 튜플 전체 파싱.
    반환: [(file_company_id, category, cert_name, grade, score, calc_type, base_score, series_filter), ...]
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = clean_md(content)
    rules = []

    for m in BONUS_RULE_RE.finditer(content):
        file_cid  = int(m.group(1))
        category  = m.group(2)
        cert_name = m.group(3)
        grade     = m.group(4)
        score     = float(m.group(5))
        calc_type = m.group(6)
        base_str  = m.group(7)
        base_score = None if base_str.upper() == "NULL" else float(base_str)
        series_f  = m.group(8)

        rules.append((file_cid, category, cert_name, grade, score, calc_type, base_score, series_f))

    return rules


def seed_real():
    """실제 공기업 자격증.md 데이터를 DB에 삽입합니다."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 이미 실제 데이터가 있으면 스킵 (한국수자원공사 존재 여부로 판단)
    if db.query(Company).filter(Company.name == "한국수자원공사").count() > 0:
        print("[OK] 실제 시드 데이터가 이미 존재합니다. 스킵합니다.")
        db.close()
        return

    md_path = find_md_file()
    if not md_path:
        print("[WARN] 공기업 자격증.md 파일을 찾을 수 없습니다. 기존 샘플 데이터를 유지합니다.")
        db.close()
        return

    print(f"[SEED] 실제 데이터 파일: {md_path}")

    try:
        # 기존 데이터 전체 삭제
        db.query(BonusRule).delete()
        db.query(Company).delete()
        db.commit()
        print("[SEED] 기존 데이터 삭제 완료")

        # ── 공기업 삽입 ──────────────────────────────────────────────────────
        company_id_map: dict[int, int] = {}   # file_id → actual_db_id

        for file_id, name, series_type, max_score, updated in COMPANY_LIST:
            c = Company(
                name=name,
                series_type=series_type,
                max_bonus_score=max_score,
                is_active=True,
                updated_at=datetime.strptime(updated, "%Y-%m-%d"),
            )
            db.add(c)
            db.flush()                # auto-increment ID 확보
            company_id_map[file_id] = c.id
            print(f"  [+] {name} (file_id={file_id} -> db_id={c.id})")

        # ── BONUS_RULE 파싱 및 삽입 ──────────────────────────────────────────
        raw_rules = parse_bonus_rules(md_path)
        print(f"[SEED] 파싱된 룰: {len(raw_rules)}개")

        rule_count = 0
        skipped = 0
        for (file_cid, category, cert_name, grade, score, calc_type, base_score, series_f) in raw_rules:
            actual_cid = company_id_map.get(file_cid)
            if actual_cid is None:
                skipped += 1
                continue

            r = BonusRule(
                company_id=actual_cid,
                category=category,
                certificate_name=cert_name,
                grade=grade,
                score=score,
                calc_type=calc_type,
                base_score=base_score,
                series_filter=series_f,
            )
            db.add(r)
            rule_count += 1

        db.commit()
        print(f"[OK] 실제 데이터 삽입 완료: 공기업 {len(COMPANY_LIST)}개, 룰 {rule_count}개 (스킵: {skipped}개)")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 실제 데이터 삽입 실패: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_real()
