/**
 * API 통신 모듈 (PRD 5.2 API 인터페이스)
 * USE_MOCK = true 시 Mock 데이터 반환 (Phase 2-B2 개발 전략)
 * Phase 3 통합 시 false로 전환
 */

// Railway 배포 주소 — 배포 후 실제 URL로 교체하세요
const API_BASE = (window.API_BASE_URL || 'RAILWAY_URL_PLACEHOLDER') + '/api';
const USE_MOCK = false; // 실제 백엔드 연동

// ── Mock 데이터 ─────────────────────────────────────────────────────────

const MOCK_CALCULATE_RESPONSE = {
  job_series: "사무직",
  results: [
    { company_id: 1, company_name: "한국전력공사", my_bonus_score: 20.0, max_bonus_score: 20, match_rate: 100.0, feedback: null },
    { company_id: 3, company_name: "국민건강보험공단", my_bonus_score: 16.0, max_bonus_score: 20, match_rate: 80.0, feedback: "'공인회계사(CPA)(1급)' 취득 시 +5.0점 추가 가능 (부족: 4.0점)" },
    { company_id: 4, company_name: "근로복지공단", my_bonus_score: 13.0, max_bonus_score: 15, match_rate: 86.7, feedback: "'공인노무사(1급)' 취득 시 +2.0점 추가 가능 (부족: 2.0점)" },
    { company_id: 5, company_name: "LH한국토지주택공사", my_bonus_score: 14.3, max_bonus_score: 20, match_rate: 71.5, feedback: "토익 990점 달성 시 어학 가산점 +0.7점 추가 가능 (부족: 5.7점)" },
    { company_id: 8, company_name: "국민연금공단", my_bonus_score: 14.3, max_bonus_score: 20, match_rate: 71.5, feedback: "'공인회계사(CPA)(1급)' 취득 시 +5.0점 추가 가능 (부족: 5.7점)" },
  ]
};

const MOCK_COMPANIES = [
  { id: 1, name: "한국전력공사", series_type: "공통", max_bonus_score: 20, is_active: true },
  { id: 2, name: "한국철도공사(KORAIL)", series_type: "공통", max_bonus_score: 20, is_active: true },
  { id: 3, name: "국민건강보험공단", series_type: "사무직", max_bonus_score: 20, is_active: true },
];

// ── API 함수 ────────────────────────────────────────────────────────────

/**
 * POST /api/calculate — 가산점 계산 요청
 */
async function calculateBonusScore(specData) {
  if (USE_MOCK) {
    await delay(800); // 로딩 UX 시뮬레이션
    return MOCK_CALCULATE_RESPONSE;
  }
  const response = await fetch(`${API_BASE}/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(specData),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.error || '서버 오류가 발생했습니다.');
  }
  return response.json();
}

/**
 * GET /api/companies — 공기업 목록 조회
 */
async function getCompanies(series = null) {
  if (USE_MOCK) {
    await delay(300);
    return MOCK_COMPANIES;
  }
  const url = new URL(`${API_BASE}/companies`);
  if (series) url.searchParams.set('series', series);
  const response = await fetch(url.toString());
  if (!response.ok) throw new ApiError(response.status, '공기업 목록 조회 실패');
  return response.json();
}

/**
 * GET /api/companies/{id}/rules — 특정 공기업 가산점 룰 조회
 */
async function getCompanyRules(companyId) {
  if (USE_MOCK) { await delay(200); return []; }
  const response = await fetch(`${API_BASE}/companies/${companyId}/rules`);
  if (!response.ok) throw new ApiError(response.status, '가산점 룰 조회 실패');
  return response.json();
}

/**
 * POST /api/admin/token — 관리자 로그인 (JWT 발급)
 */
async function adminLogin(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  const response = await fetch(`${API_BASE}/admin/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '로그인 실패');
  }
  return response.json();
}

/**
 * PUT /api/admin/companies/{id} — 관리자: 공기업 정보 수정
 */
async function adminUpdateCompany(companyId, updateData, token) {
  const response = await fetch(`${API_BASE}/admin/companies/${companyId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '수정 실패');
  }
  return response.json();
}

/**
 * POST /api/admin/sync — 관리자: 외부 API 동기화
 */
async function adminSync(token) {
  const response = await fetch(`${API_BASE}/admin/sync`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '동기화 실패');
  }
  return response.json();
}

/**
 * GET /api/admin/companies — 관리자: 전체 공기업 목록
 */
async function adminGetCompanies(token) {
  const response = await fetch(`${API_BASE}/admin/companies`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '조회 실패');
  }
  return response.json();
}

/**
 * GET /api/admin/logs — 관리자: 변경 이력 조회
 */
async function adminGetLogs(token) {
  const response = await fetch(`${API_BASE}/admin/logs`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) throw new ApiError(response.status, '이력 조회 실패');
  return response.json();
}

// ── 유틸리티 ────────────────────────────────────────────────────────────

class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 전역 노출
window.API = {
  calculateBonusScore,
  getCompanies,
  getCompanyRules,
  adminLogin,
  adminUpdateCompany,
  adminSync,
  adminGetCompanies,
  adminGetLogs,
  ApiError,
};
