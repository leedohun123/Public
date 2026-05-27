/**
 * API 통신 모듈
 * 백엔드 서버 없이 브라우저에서 직접 계산 (engine.js + data.js 사용)
 * 서버 연동이 필요하면 USE_LOCAL_ENGINE = false 로 변경
 */

const USE_LOCAL_ENGINE = true;  // true = 로컬 JS 엔진 사용 (서버 불필요)
const API_BASE = 'http://localhost:8000/api';  // USE_LOCAL_ENGINE=false 시에만 사용

// ── 로컬 관리자 설정 ────────────────────────────────────────────────────
const _ADMIN_USER = 'admin';
const _ADMIN_PASS = 'admin1234';
const _LS_COMPANIES = 'gasan_companies';
const _LS_RULES     = 'gasan_rules';
const _LS_LOGS      = 'gasan_logs';

function _createLocalToken() {
  return btoa(JSON.stringify({ user: 'admin', iat: Date.now() }));
}
function _validateToken(token) {
  return typeof token === 'string' && token.length > 0;
}

// ── localStorage 헬퍼 ────────────────────────────────────────────────────
function _loadCompanies() {
  try {
    const s = localStorage.getItem(_LS_COMPANIES);
    if (s) return JSON.parse(s);
  } catch (_) {}
  return null;
}
function _loadRules() {
  try {
    const s = localStorage.getItem(_LS_RULES);
    if (s) return JSON.parse(s);
  } catch (_) {}
  return null;
}
function _saveCompanies(arr) {
  localStorage.setItem(_LS_COMPANIES, JSON.stringify(arr));
  // 메모리의 COMPANIES_DATA도 갱신
  if (typeof COMPANIES_DATA !== 'undefined') {
    COMPANIES_DATA.length = 0;
    arr.forEach(c => COMPANIES_DATA.push(c));
  }
}
function _saveRules(arr) {
  localStorage.setItem(_LS_RULES, JSON.stringify(arr));
  // 메모리의 BONUS_RULES_DATA도 갱신
  if (typeof BONUS_RULES_DATA !== 'undefined') {
    BONUS_RULES_DATA.length = 0;
    arr.forEach(r => BONUS_RULES_DATA.push(r));
  }
}
function _appendLog(action, companyId, detail) {
  const logs = _loadLogs();
  logs.unshift({
    id: Date.now(),
    action,
    company_id: companyId ?? null,
    changed_by: 'admin',
    detail: detail || '',
    created_at: new Date().toISOString(),
  });
  localStorage.setItem(_LS_LOGS, JSON.stringify(logs.slice(0, 100)));
}
function _loadLogs() {
  try {
    const s = localStorage.getItem(_LS_LOGS);
    if (s) return JSON.parse(s);
  } catch (_) {}
  return [];
}

/** COMPANIES_DATA를 admin API 응답 형식으로 변환 */
function _toApiCompany(c) {
  return {
    id:              c.id,
    name:            c.name,
    series_type:     c.seriesType  ?? c.series_type  ?? '공통',
    max_bonus_score: c.maxBonusScore ?? c.max_bonus_score ?? 0,
    is_active:       c.isActive    ?? c.is_active    ?? true,
  };
}

/** BONUS_RULES_DATA를 admin API 응답 형식으로 변환 */
function _toApiRule(r) {
  return {
    id:               r.id,
    company_id:       r.companyId       ?? r.company_id,
    category:         r.category,
    certificate_name: r.certificateName ?? r.certificate_name,
    grade:            r.grade,
    score:            r.score,
    calc_type:        r.calcType        ?? r.calc_type  ?? 'FIXED',
    base_score:       r.baseScore       ?? r.base_score ?? null,
    series_filter:    r.seriesFilter    ?? r.series_filter ?? '공통',
  };
}

/** admin 저장 payload → 내부 camelCase 포맷 */
function _fromApiRule(r, companyId, idx) {
  return {
    id:               (companyId * 10000) + idx,
    companyId,
    category:         r.category,
    certificateName:  r.certificate_name,
    grade:            r.grade,
    score:            r.score,
    calcType:         r.calc_type  ?? 'FIXED',
    baseScore:        r.base_score ?? null,
    seriesFilter:     r.series_filter ?? '공통',
  };
}

// ── API 함수 ────────────────────────────────────────────────────────────

/**
 * POST /api/calculate — 가산점 계산 요청
 */
async function calculateBonusScore(specData) {
  if (USE_LOCAL_ENGINE) {
    await delay(300);

    // localStorage 수정 데이터가 있으면 엔진에 반영
    const localCompanies = _loadCompanies();
    const localRules     = _loadRules();
    if (localCompanies && typeof COMPANIES_DATA !== 'undefined') {
      COMPANIES_DATA.length = 0;
      localCompanies.forEach(c => COMPANIES_DATA.push(c));
    }
    if (localRules && typeof BONUS_RULES_DATA !== 'undefined') {
      BONUS_RULES_DATA.length = 0;
      localRules.forEach(r => BONUS_RULES_DATA.push(r));
    }

    const certs = (specData.certificates || []).map(c => ({ name: c.name, grade: c.grade }));
    const lang = {
      toeic:        specData.language_scores?.toeic         || null,
      toeicSpeaking: specData.language_scores?.toeic_speaking || null,
      opic:         specData.language_scores?.opic          || null,
    };

    const engineResults = Engine.runEngine(specData.job_series, certs, lang);

    if (engineResults.length === 0) {
      throw new ApiError(404, '해당 직렬에 등록된 공기업 데이터가 없습니다.');
    }

    return {
      job_series: specData.job_series,
      results: engineResults.map(r => ({
        company_id:      r.companyId,
        company_name:    r.companyName,
        my_bonus_score:  r.myBonusScore,
        max_bonus_score: r.maxBonusScore,
        match_rate:      r.matchRate,
        feedback:        r.feedback,
      })),
    };
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
  if (USE_LOCAL_ENGINE) {
    await delay(200);
    const src = _loadCompanies() || COMPANIES_DATA;
    const list = src.filter(c => {
      const active = c.isActive ?? c.is_active ?? true;
      const st     = c.seriesType ?? c.series_type ?? '공통';
      return active && (!series || st === '공통' || st === series);
    });
    return list.map(_toApiCompany);
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
    const src = _loadRules() || BONUS_RULES_DATA;
    return src
      .filter(r => (r.companyId ?? r.company_id) === companyId)
      .map(_toApiRule);
  }
  const response = await fetch(`${API_BASE}/companies/${companyId}/rules`);
  if (!response.ok) throw new ApiError(response.status, '가산점 룰 조회 실패');
  return response.json();
}

// ── 관리자 API ──────────────────────────────────────────────────────────

async function adminLogin(username, password) {
  if (USE_LOCAL_ENGINE) {
    await delay(500);
    if (username === _ADMIN_USER && password === _ADMIN_PASS) {
      return { access_token: _createLocalToken(), token_type: 'bearer' };
    }
    throw new ApiError(401, '아이디 또는 비밀번호가 올바르지 않습니다.');
  }

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

async function adminGetCompanies(token) {
  if (USE_LOCAL_ENGINE) {
    await delay(200);
    if (!_validateToken(token)) throw new ApiError(401, '인증이 필요합니다.');
    const src = _loadCompanies() || COMPANIES_DATA;
    return src.map(_toApiCompany);
  }
  const response = await fetch(`${API_BASE}/admin/companies`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '조회 실패');
  }
  return response.json();
}

async function adminUpdateCompany(companyId, updateData, token) {
  if (USE_LOCAL_ENGINE) {
    await delay(300);
    if (!_validateToken(token)) throw new ApiError(401, '인증이 필요합니다.');

    let companies = (_loadCompanies() || COMPANIES_DATA).map(c => ({ ...c }));
    const idx = companies.findIndex(c => (c.id ?? c.id) === companyId);
    if (idx === -1) throw new ApiError(404, '기업을 찾을 수 없습니다.');

    companies[idx] = {
      id:             companyId,
      name:           updateData.name,
      seriesType:     updateData.series_type,
      maxBonusScore:  updateData.max_bonus_score,
      isActive:       updateData.is_active,
    };
    _saveCompanies(companies);

    // 룰 교체
    let rules = (_loadRules() || BONUS_RULES_DATA).filter(
      r => (r.companyId ?? r.company_id) !== companyId
    );
    const newRules = (updateData.bonus_rules || []).map((r, i) =>
      _fromApiRule(r, companyId, i)
    );
    _saveRules([...rules, ...newRules]);

    _appendLog('MANUAL_UPDATE', companyId, `${updateData.name} 정보 수정`);
    return { id: companyId, ...updateData };
  }

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

async function adminAddCompany(updateData, token) {
  if (USE_LOCAL_ENGINE) {
    await delay(300);
    if (!_validateToken(token)) throw new ApiError(401, '인증이 필요합니다.');

    const companies = (_loadCompanies() || COMPANIES_DATA).map(c => ({ ...c }));
    const newId = Math.max(0, ...companies.map(c => c.id ?? 0)) + 1;

    companies.push({
      id:            newId,
      name:          updateData.name,
      seriesType:    updateData.series_type,
      maxBonusScore: updateData.max_bonus_score,
      isActive:      updateData.is_active,
    });
    _saveCompanies(companies);

    const rules = _loadRules() || BONUS_RULES_DATA.map(r => ({ ...r }));
    const newRules = (updateData.bonus_rules || []).map((r, i) =>
      _fromApiRule(r, newId, i)
    );
    _saveRules([...rules, ...newRules]);

    _appendLog('MANUAL_ADD', newId, `${updateData.name} 신규 등록`);
    return { id: newId, ...updateData };
  }

  const response = await fetch(`${API_BASE}/admin/companies`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(updateData),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new ApiError(response.status, err.detail || '등록 실패');
  }
  return response.json();
}

async function adminSync(token) {
  if (USE_LOCAL_ENGINE) {
    await delay(800);
    if (!_validateToken(token)) throw new ApiError(401, '인증이 필요합니다.');
    _appendLog('AUTO_SYNC', null, '로컬 엔진 동기화 완료 (data.js 기준)');
    return { status: 'success', message: '로컬 데이터 동기화 완료' };
  }

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

async function adminGetLogs(token) {
  if (USE_LOCAL_ENGINE) {
    await delay(100);
    if (!_validateToken(token)) throw new ApiError(401, '인증이 필요합니다.');
    return _loadLogs();
  }

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
  adminGetCompanies,
  adminUpdateCompany,
  adminAddCompany,
  adminSync,
  adminGetLogs,
  ApiError,
};
