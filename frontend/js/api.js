/**
 * API 통신 모듈
 * 백엔드 서버 없이 브라우저에서 직접 계산 (engine.js + data.js 사용)
 * 서버 연동이 필요하면 USE_LOCAL_ENGINE = false 로 변경
 */

const USE_LOCAL_ENGINE = true;  // true = 로컬 JS 엔진 사용 (서버 불필요)
const API_BASE = 'http://localhost:8000/api';  // USE_LOCAL_ENGINE=false 시에만 사용

// ── API 함수 ────────────────────────────────────────────────────────────

/**
 * POST /api/calculate — 가산점 계산 요청
 * USE_LOCAL_ENGINE=true 시 JS 엔진으로 직접 계산
 */
async function calculateBonusScore(specData) {
  if (USE_LOCAL_ENGINE) {
    // 브라우저에서 직접 계산 (서버 필요 없음)
    await delay(300); // UX 로딩 시뮬레이션

    const certs = (specData.certificates || []).map(c => ({ name: c.name, grade: c.grade }));
    const lang = {
      toeic: specData.language_scores?.toeic || null,
      toeicSpeaking: specData.language_scores?.toeic_speaking || null,
      opic: specData.language_scores?.opic || null,
    };

    const engineResults = Engine.runEngine(specData.job_series, certs, lang);

    if (engineResults.length === 0) {
      throw new ApiError(404, '해당 직렬에 등록된 공기업 데이터가 없습니다.');
    }

    return {
      job_series: specData.job_series,
      results: engineResults.map(r => ({
        company_id: r.companyId,
        company_name: r.companyName,
        my_bonus_score: r.myBonusScore,
        max_bonus_score: r.maxBonusScore,
        match_rate: r.matchRate,
        feedback: r.feedback,
      })),
    };
  }

  // 서버 연동 모드 (USE_LOCAL_ENGINE=false 시)
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
  if (USE_LOCAL_ENGINE) {
    await delay(200);
    const list = COMPANIES_DATA.filter(c =>
      c.isActive && (!series || c.seriesType === "공통" || c.seriesType === series)
    );
    return list.map(c => ({
      id: c.id,
      name: c.name,
      series_type: c.seriesType,
      max_bonus_score: c.maxBonusScore,
      is_active: c.isActive,
    }));
  }
  const url = new URL(`${API_BASE}/companies`);
  if (series) url.searchParams.set('series', series);
  const response = await fetch(url.toString());
  if (!response.ok) throw new ApiError(response.status, '공기업 목록 조회 실패');
  return response.json();
}

/**
 * GET /api/companies/{id}/rules
 */
async function getCompanyRules(companyId) {
  if (USE_LOCAL_ENGINE) {
    await delay(100);
    return BONUS_RULES_DATA
      .filter(r => r.companyId === companyId)
      .map(r => ({
        id: r.id, company_id: r.companyId,
        category: r.category, certificate_name: r.certificateName,
        grade: r.grade, score: r.score,
        calc_type: r.calcType, base_score: r.baseScore,
        series_filter: r.seriesFilter,
      }));
  }
  const response = await fetch(`${API_BASE}/companies/${companyId}/rules`);
  if (!response.ok) throw new ApiError(response.status, '가산점 룰 조회 실패');
  return response.json();
}

/**
 * 관리자 API — 서버 연동 시에만 동작 (로컬 엔진 모드에서는 미지원)
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
