# 🏢 공기업 가산점 자동 계산 및 매칭 시스템

> PRD.md · TASK.md · 요구사항명세서.md 기반 구현

---

## 📌 시스템 개요

취업 준비생이 보유한 **자격증·어학 스펙**을 입력하면, 전국 공기업별 가산점을 자동으로 계산하고  
**매칭률 기반으로 최적 공기업을 추천**해 주는 웹 시스템입니다.

---

## 🏗️ 기술 스택

| 구분 | 기술 |
|------|------|
| **백엔드** | Python 3.x + FastAPI + SQLAlchemy |
| **DB** | SQLite (개발) / PostgreSQL (운영) |
| **인증** | JWT (python-jose) |
| **프론트엔드** | HTML5 + CSS3 + Vanilla JS |
| **API 문서** | Swagger UI (자동 생성) |

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
# 프로젝트 루트에 .env 파일이 이미 생성되어 있습니다.
# 운영 배포 시 SECRET_KEY를 반드시 변경하세요.
```

### 3. 서버 실행

```bash
cd backend
python main.py
```

서버 시작 시 자동으로:
- DB 테이블 생성
- 샘플 공기업 10개 + 가산점 룰 데이터 삽입

### 4. 접속

| URL | 설명 |
|-----|------|
| `http://localhost:8000` | 메인 화면 (스펙 입력 & 결과) |
| `http://localhost:8000/admin.html` | 관리자 대시보드 |
| `http://localhost:8000/docs` | Swagger API 문서 |
| `http://localhost:8000/redoc` | ReDoc API 문서 |

### 5. 관리자 로그인

- **아이디**: `admin`
- **비밀번호**: `admin1234`

---

## 📊 핵심 기능

### 가산점 연산 룰 엔진 (REQ-004)

| 룰 | 설명 |
|----|------|
| **OR 룰** | 동일 계열 자격증 중 최고 등급 1개만 반영 |
| **비례 연산** | `(유저점수 / 만점기준) × 배점` |
| **합산 한도(Cap)** | 기업별 최대 가산점 초과분 절삭 |
| **매칭률** | `(내 가산점 / 최대 가산점) × 100` |

### 샘플 공기업 (10개)

| 공기업 | 직렬 | 최대 가산점 |
|--------|------|-----------|
| 한국전력공사 | 공통 | 20점 |
| 한국철도공사(KORAIL) | 공통 | 20점 |
| 국민건강보험공단 | 사무직 | 20점 |
| 근로복지공단 | 사무직 | 15점 |
| LH한국토지주택공사 | 공통 | 20점 |
| 한국수자원공사 | 공통 | 18점 |
| 한국도로공사 | 공통 | 20점 |
| 국민연금공단 | 사무직 | 20점 |
| 한국산업인력공단 | 사무직 | 15점 |
| 한국가스공사 | 기술직 | 20점 |

---

## 🧪 테스트 실행

```bash
cd backend
python -m pytest tests/ -v
```

OR 룰, 어학 비례 연산, Cap 절삭, 매칭률, 피드백 생성 등 핵심 시나리오를 검증합니다.

---

## 📁 프로젝트 구조

```
project/
├── backend/
│   ├── app/
│   │   ├── api/          # REST API 라우터 (calculate, companies, admin)
│   │   ├── engine/       # 가산점 룰 연산 엔진 (독립 모듈)
│   │   ├── models/       # SQLAlchemy ORM 모델
│   │   ├── services/     # 비즈니스 로직
│   │   ├── external/     # 외부 API 연동 (잡알리오)
│   │   ├── auth.py       # JWT 인증
│   │   └── database.py   # DB 연결 설정
│   ├── tests/            # 단위 테스트
│   ├── seed_data.py      # 샘플 데이터 삽입
│   ├── main.py           # FastAPI 앱 진입점
│   └── requirements.txt
├── frontend/
│   ├── index.html        # 메인 화면 (스펙 입력 & 결과)
│   ├── admin.html        # 관리자 대시보드
│   ├── css/style.css     # 반응형 스타일
│   └── js/
│       ├── api.js        # API 통신 모듈
│       ├── main.js       # 메인 인터랙션 로직
│       └── admin.js      # 관리자 로직
├── .env                  # 환경 변수
├── .env.example          # 환경 변수 예시
└── README.md
```

---

## 🔐 API 엔드포인트

| Method | Endpoint | 인증 | 설명 |
|--------|----------|------|------|
| `POST` | `/api/calculate` | 불필요 | 가산점 계산 |
| `GET` | `/api/companies` | 불필요 | 공기업 목록 |
| `GET` | `/api/companies/{id}/rules` | 불필요 | 가산점 룰 조회 |
| `POST` | `/api/admin/token` | 불필요 | 관리자 로그인 |
| `PUT` | `/api/admin/companies/{id}` | JWT 필수 | 공기업 수정 |
| `POST` | `/api/admin/sync` | JWT 필수 | 외부 API 동기화 |
| `GET` | `/api/admin/logs` | JWT 필수 | 변경 이력 조회 |

---

## ✅ 구현된 요구사항 (REQ)

| REQ ID | 항목 | 상태 |
|--------|------|------|
| REQ-001 | 직렬 선택 및 공기업 필터링 | ✅ 구현완료 |
| REQ-002 | 자격증 종류·급수 입력 UI | ✅ 구현완료 |
| REQ-003 | 어학 성적 정량 입력 | ✅ 구현완료 |
| REQ-004 | 가산점 연산 룰 엔진 (OR/비례/Cap) | ✅ 구현완료 |
| REQ-005 | 매칭률 계산 및 내림차순 정렬 | ✅ 구현완료 |
| REQ-006 | 스펙 보완 개인 맞춤 피드백 | ✅ 구현완료 |
| REQ-007 | 관리자 DB 수동 업데이트 | ✅ 구현완료 |
| REQ-008 | 외부 API 자동 동기화 | ✅ 구현완료 (Demo 모드) |
