/**
 * 관리자 대시보드 JS (PRD REQ-007, SRS UC-007~008)
 * JWT 인증 후 공기업 가산점 DB 관리 기능 제공
 */

let adminToken = null;
let companiesCache = [];

// ── 초기화 ──────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // 저장된 토큰 확인
  adminToken = sessionStorage.getItem('admin_token');
  if (adminToken) {
    showDashboard();
    loadCompanies();
    loadLogs();
  }

  document.getElementById('login-form').addEventListener('submit', onLogin);
  document.getElementById('btn-logout').addEventListener('click', onLogout);
  document.getElementById('btn-sync').addEventListener('click', onSync);
  document.getElementById('btn-add-company').addEventListener('click', () => showCompanyModal(null));
  document.getElementById('modal-close').addEventListener('click', closeModal);
  document.getElementById('company-form').addEventListener('submit', onSaveCompany);
  document.getElementById('btn-add-rule').addEventListener('click', addRuleRow);
});

// ── 로그인 (UC-007 사전 조건) ───────────────────────────────────────────

async function onLogin(e) {
  e.preventDefault();
  const username = document.getElementById('admin-username').value;
  const password = document.getElementById('admin-password').value;
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';

  try {
    const result = await API.adminLogin(username, password);
    adminToken = result.access_token;
    sessionStorage.setItem('admin_token', adminToken);
    showDashboard();
    loadCompanies();
    loadLogs();
    showToast('관리자 로그인 성공', 'success');
  } catch (err) {
    errEl.textContent = '⚠ ' + (err.message || '로그인 실패');
  }
}

function onLogout() {
  adminToken = null;
  sessionStorage.removeItem('admin_token');
  document.getElementById('login-section').style.display = '';
  document.getElementById('dashboard-section').style.display = 'none';
  showToast('로그아웃 되었습니다.', 'info');
}

function showDashboard() {
  document.getElementById('login-section').style.display = 'none';
  document.getElementById('dashboard-section').style.display = '';
}

// ── 공기업 목록 조회 ────────────────────────────────────────────────────

async function loadCompanies() {
  try {
    companiesCache = await API.adminGetCompanies(adminToken);
    renderCompanyTable(companiesCache);
  } catch (err) {
    if (err.status === 401) { onLogout(); return; }
    showToast('공기업 목록 조회 실패: ' + err.message, 'error');
  }
}

function renderCompanyTable(companies) {
  const tbody = document.getElementById('company-table-body');
  tbody.innerHTML = '';
  if (!companies.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--gray-400);padding:24px;">등록된 공기업이 없습니다.</td></tr>`;
    return;
  }
  companies.forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${c.id}</td>
      <td><strong>${escapeHtml(c.name)}</strong></td>
      <td>${c.series_type}</td>
      <td>${c.max_bonus_score}점</td>
      <td>
        <span class="status-badge ${c.is_active ? 'active' : 'inactive'}">${c.is_active ? '활성' : '비활성'}</span>
      </td>
      <td>
        <button class="btn-sm btn-edit" onclick="showCompanyModal(${c.id})">✏️ 수정</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ── 공기업 수정 모달 ────────────────────────────────────────────────────

async function showCompanyModal(companyId) {
  const modal = document.getElementById('company-modal');
  const form = document.getElementById('company-form');
  const modalTitle = document.getElementById('modal-title');
  const rulesBody = document.getElementById('rules-body');

  form.dataset.companyId = companyId || '';
  rulesBody.innerHTML = '';

  if (companyId) {
    // 기존 공기업 수정
    modalTitle.textContent = '공기업 가산점 수정';
    const company = companiesCache.find(c => c.id === companyId);
    if (company) {
      document.getElementById('f-name').value = company.name;
      document.getElementById('f-series').value = company.series_type;
      document.getElementById('f-max-score').value = company.max_bonus_score;
      document.getElementById('f-active').checked = company.is_active;
    }
    try {
      const rules = await API.getCompanyRules(companyId);
      rules.forEach(r => addRuleRow(r));
    } catch (_) {}
  } else {
    // 신규 등록
    modalTitle.textContent = '공기업 신규 등록';
    form.reset();
    document.getElementById('f-active').checked = true;
    addRuleRow();
  }

  modal.style.display = 'flex';
}

function closeModal() {
  document.getElementById('company-modal').style.display = 'none';
}

// ── 가산점 룰 행 추가 ───────────────────────────────────────────────────

function addRuleRow(rule = {}) {
  const tbody = document.getElementById('rules-body');
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td><input type="text" class="r-category" placeholder="IT/어학/역사/경영" value="${rule.category || ''}" /></td>
    <td><input type="text" class="r-cert-name" placeholder="자격증명" value="${rule.certificate_name || ''}" /></td>
    <td><input type="text" class="r-grade" placeholder="1급/IH" value="${rule.grade || ''}" /></td>
    <td><input type="number" class="r-score" placeholder="0.0" step="0.5" min="0" value="${rule.score ?? ''}" /></td>
    <td>
      <select class="r-calc-type">
        <option value="FIXED" ${rule.calc_type !== 'PROPORTIONAL' ? 'selected' : ''}>FIXED</option>
        <option value="PROPORTIONAL" ${rule.calc_type === 'PROPORTIONAL' ? 'selected' : ''}>PROPORTIONAL</option>
      </select>
    </td>
    <td><input type="number" class="r-base-score" placeholder="990" min="0" value="${rule.base_score || ''}" /></td>
    <td>
      <select class="r-series-filter">
        <option value="공통" ${(rule.series_filter || '공통') === '공통' ? 'selected' : ''}>공통</option>
        <option value="사무직" ${rule.series_filter === '사무직' ? 'selected' : ''}>사무직</option>
        <option value="기술직" ${rule.series_filter === '기술직' ? 'selected' : ''}>기술직</option>
      </select>
    </td>
    <td><button type="button" class="btn-sm btn-delete-rule" onclick="this.closest('tr').remove()">✕</button></td>
  `;
  tbody.appendChild(tr);
}

// ── 공기업 저장 ─────────────────────────────────────────────────────────

async function onSaveCompany(e) {
  e.preventDefault();
  const companyId = document.getElementById('company-form').dataset.companyId;
  const name = document.getElementById('f-name').value.trim();
  const series_type = document.getElementById('f-series').value;
  const max_bonus_score = parseInt(document.getElementById('f-max-score').value);
  const is_active = document.getElementById('f-active').checked;

  if (!name || !series_type || isNaN(max_bonus_score)) {
    showToast('필수 항목을 모두 입력해 주세요.', 'error');
    return;
  }

  // 룰 수집
  const bonus_rules = [];
  document.querySelectorAll('#rules-body tr').forEach(tr => {
    const category = tr.querySelector('.r-category').value.trim();
    const certificate_name = tr.querySelector('.r-cert-name').value.trim();
    const grade = tr.querySelector('.r-grade').value.trim();
    const score = parseFloat(tr.querySelector('.r-score').value);
    const calc_type = tr.querySelector('.r-calc-type').value;
    const base_score_val = tr.querySelector('.r-base-score').value;
    const base_score = base_score_val ? parseInt(base_score_val) : null;
    const series_filter = tr.querySelector('.r-series-filter').value;
    if (category && certificate_name && grade && !isNaN(score)) {
      bonus_rules.push({ category, certificate_name, grade, score, calc_type, base_score, series_filter });
    }
  });

  const payload = { name, series_type, max_bonus_score, is_active, bonus_rules };

  try {
    if (companyId) {
      await API.adminUpdateCompany(parseInt(companyId), payload, adminToken);
      showToast('공기업 정보가 수정되었습니다.', 'success');
    } else {
      const response = await fetch(`http://localhost:8000/api/admin/companies`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${adminToken}`,
        },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || '등록 실패');
      }
      showToast('공기업이 신규 등록되었습니다.', 'success');
    }
    closeModal();
    loadCompanies();
    loadLogs();
  } catch (err) {
    if (err.status === 401 || err.message?.includes('401')) { onLogout(); return; }
    showToast('저장 실패: ' + err.message, 'error');
  }
}

// ── 외부 API 동기화 (UC-008) ────────────────────────────────────────────

async function onSync() {
  const btn = document.getElementById('btn-sync');
  btn.disabled = true;
  btn.textContent = '⏳ 동기화 중...';
  try {
    const result = await API.adminSync(adminToken);
    showToast(`동기화 완료: ${result.message}`, result.status === 'success' ? 'success' : 'error');
    loadLogs();
  } catch (err) {
    if (err.status === 401) { onLogout(); return; }
    showToast('동기화 실패: ' + err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 DB 동기화 실행';
  }
}

// ── 변경 이력 조회 ──────────────────────────────────────────────────────

async function loadLogs() {
  try {
    const logs = await API.adminGetLogs(adminToken);
    renderLogs(logs);
  } catch (err) {}
}

function renderLogs(logs) {
  const tbody = document.getElementById('log-table-body');
  tbody.innerHTML = '';
  if (!logs.length) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:var(--gray-400);padding:16px;">변경 이력이 없습니다.</td></tr>`;
    return;
  }
  logs.slice(0, 20).forEach(log => {
    const tr = document.createElement('tr');
    const date = new Date(log.created_at).toLocaleString('ko-KR');
    tr.innerHTML = `
      <td>${date}</td>
      <td><span class="badge-action ${log.action === 'AUTO_SYNC' ? 'sync' : 'manual'}">${log.action}</span></td>
      <td>${log.company_id ?? '-'}</td>
      <td>${escapeHtml(log.changed_by)}</td>
      <td style="font-size:0.8rem;color:var(--gray-600);">${escapeHtml(log.detail || '-')}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ── 유틸 ────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const icons = { error: '❌', success: '✅', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-icon">${icons[type] || 'ℹ️'}</span><span>${escapeHtml(message)}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('closing');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

window.showCompanyModal = showCompanyModal;
window.addRuleRow = addRuleRow;
