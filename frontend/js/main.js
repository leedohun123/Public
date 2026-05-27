/**
 * 공기업 가산점 매칭 시스템 — 메인 JS 로직
 * PRD 5.1 와이어프레임 / SRS UC-001~006 기반 구현
 */

// ── 데이터 상수 ─────────────────────────────────────────────────────────

// ── 자격증 목록 (실제 공기업 자격증.md 기준 2026년 데이터) ──────────────
// grade 값은 DB BonusRule.grade와 정확히 일치해야 가산점이 계산됩니다.
const CERTIFICATES = [
  // ── IT·정보 ──────────────────────────────────────────────────────
  { name: "컴퓨터활용능력", grades: ["1급", "2급", "3급"] },
  { name: "정보처리기사", grades: ["기사"] },
  { name: "정보처리산업기사", grades: ["산업기사"] },
  { name: "사무자동화산업기사", grades: ["산업기사"] },
  { name: "워드프로세서", grades: ["1급"] },
  { name: "빅데이터분석기사", grades: ["기사"] },
  { name: "정보보안기사", grades: ["기사"] },
  { name: "정보통신기사", grades: ["기사"] },
  { name: "임베디드기사", grades: ["기사"] },
  { name: "전자계산기조직응용기사", grades: ["기사"] },
  { name: "전자기사", grades: ["기사"] },
  { name: "ITQ", grades: ["A등급", "B등급"] },
  { name: "데이터분석전문가", grades: ["-"] },
  { name: "데이터분석준전문가", grades: ["-"] },
  // ── 한국사·국어 ──────────────────────────────────────────────────
  { name: "한국사능력검정시험", grades: ["1급", "2급", "3급"] },
  { name: "KBS한국어능력", grades: ["1급", "2+급", "2-급", "3+급"] },
  { name: "국어능력인증", grades: ["1급", "2급", "3~5급"] },
  { name: "한국실용글쓰기", grades: ["1급", "2급", "준2급", "3급", "준3급"] },
  // ── 경영·회계·금융 ───────────────────────────────────────────────
  { name: "공인회계사", grades: ["기사급", "기술사급"] },
  { name: "세무사", grades: ["기사급", "기술사급"] },
  { name: "공인노무사", grades: ["기사급", "기술사급"] },
  { name: "경영지도사", grades: ["기사급"] },
  { name: "감정평가사", grades: ["기사급"] },
  { name: "변호사", grades: ["기술사급"] },
  { name: "변리사", grades: ["기술사급"] },
  { name: "법무사", grades: ["기능장급"] },
  { name: "재경관리사", grades: ["-"] },
  { name: "전산세무", grades: ["1급", "2급"] },
  { name: "전산회계운용사", grades: ["1급", "2급"] },
  { name: "회계관리", grades: ["1급"] },
  { name: "물류관리사", grades: ["기사급"] },
  { name: "유통관리사", grades: ["1급", "2급"] },
  { name: "사회조사분석사", grades: ["1급", "2급"] },
  // ── 전기 ─────────────────────────────────────────────────────────
  { name: "전기기사", grades: ["기사"] },
  { name: "전기산업기사", grades: ["산업기사"] },
  { name: "전기공사기사", grades: ["기사"] },
  { name: "전기기능장", grades: ["기능장"] },
  { name: "소방설비기사(전기)", grades: ["기사"] },
  // ── 기계 ─────────────────────────────────────────────────────────
  { name: "일반기계기사", grades: ["기사"] },
  { name: "기계설계기사", grades: ["기사"] },
  { name: "공조냉동기계기사", grades: ["기사"] },
  { name: "건설기계설비기사", grades: ["기사"] },
  { name: "메카트로닉스기사", grades: ["기사"] },
  { name: "소방설비기사(기계)", grades: ["기사"] },
  { name: "설비보전기사", grades: ["기사"] },
  { name: "에너지관리기사", grades: ["기사"] },
  { name: "용접기사", grades: ["기사"] },
  { name: "비파괴검사기사", grades: ["기사"] },
  // ── 화학·환경 ────────────────────────────────────────────────────
  { name: "화공기사", grades: ["기사"] },
  { name: "대기환경기사", grades: ["기사"] },
  { name: "수질환경기사", grades: ["기사"] },
  { name: "폐기물처리기사", grades: ["기사"] },
  { name: "소음진동기사", grades: ["기사"] },
  { name: "온실가스관리기사", grades: ["기사"] },
  { name: "토양환경기사", grades: ["기사"] },
  { name: "산업안전기사", grades: ["기사"] },
  { name: "산업안전산업기사", grades: ["산업기사"] },
  { name: "가스기사", grades: ["기사"] },
  { name: "가스산업기사", grades: ["산업기사"] },
  // ── 토목·건설 ────────────────────────────────────────────────────
  { name: "토목기사", grades: ["기사"] },
  { name: "토목산업기사", grades: ["산업기사"] },
  { name: "건설안전기사", grades: ["기사"] },
  { name: "건설안전산업기사", grades: ["산업기사"] },
  { name: "건설재료시험기사", grades: ["기사"] },
  { name: "콘크리트기사", grades: ["기사"] },
  { name: "측량및지형공간정보기사", grades: ["기사"] },
  { name: "지적기사", grades: ["기사"] },
  { name: "도시계획기사", grades: ["기사"] },
  { name: "응용지질기사", grades: ["기사"] },
  // ── 건축 ─────────────────────────────────────────────────────────
  { name: "건축기사", grades: ["기사"] },
  { name: "건축산업기사", grades: ["산업기사"] },
  { name: "실내건축기사", grades: ["기사"] },
  { name: "건축설비기사", grades: ["기사"] },
  { name: "건축사", grades: ["-"] },
  { name: "조경기사", grades: ["기사"] },
  // ── 안전 ─────────────────────────────────────────────────────────
  { name: "산업위생관리기사", grades: ["기사"] },
  { name: "인간공학기사", grades: ["기사"] },
  // ── 전문자격 (기술사급) ───────────────────────────────────────────
  { name: "기술사", grades: ["기술사"] },
  { name: "건축사", grades: ["-"] },
];

const OPIC_GRADES = ["", "NL", "IL", "IM1", "IM2", "IM3", "IH", "AL"];
const TOEIC_SPEAKING_LEVELS = ["", "Lv.1", "Lv.2", "Lv.3", "Lv.4", "Lv.5", "Lv.6", "Lv.7", "Lv.8"];

// ── 상태 ────────────────────────────────────────────────────────────────

let selectedSeries = null;  // "사무직" | "기술직"
let lastInputState = null;  // 스펙 수정 후 복귀 시 입력값 유지용

// ── DOM 참조 ─────────────────────────────────────────────────────────────

const inputSection = document.getElementById('input-section');
const resultSection = document.getElementById('result-section');
const certTableBody = document.getElementById('cert-table-body');
const btnCalculate = document.getElementById('btn-calculate');
const btnBack = document.getElementById('btn-back');
const toastContainer = document.getElementById('toast-container');
const resultTableBody = document.getElementById('result-table-body');
const resultTitle = document.getElementById('result-title');
const resultSubtitle = document.getElementById('result-subtitle');
const summaryTotal = document.getElementById('summary-total');
const summaryPerfect = document.getElementById('summary-perfect');
const summaryAvg = document.getElementById('summary-avg');

// ── 초기화 ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  addCertRow();          // 초기 자격증 행 1개
  bindSeriesButtons();
  btnCalculate.addEventListener('click', onCalculate);
  btnBack.addEventListener('click', onBack);
});

// ── 직렬 선택 (UC-001) ── 드롭다운 방식 ────────────────────────────────

function bindSeriesButtons() {
  // 드롭다운 방식
  const seriesSelect = document.getElementById('series-select');
  if (seriesSelect) {
    seriesSelect.addEventListener('change', () => {
      selectedSeries = seriesSelect.value || null;
      if (selectedSeries) {
        seriesSelect.classList.add('selected');
        clearError('series-error');
      } else {
        seriesSelect.classList.remove('selected');
      }
    });
  }
  // 구버전 버튼 방식 (하위 호환)
  document.querySelectorAll('.series-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.series-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedSeries = btn.dataset.series;
      clearError('series-error');
    });
  });
}

// ── 자격증 행 동적 추가/삭제 (UC-002) ────────────────────────────────────

function addCertRow(certName = '', grade = '') {
  const row = document.createElement('div');
  row.className = 'cert-row';
  row.innerHTML = `
    <select class="cert-name-select" onchange="onCertNameChange(this)">
      <option value="">자격증 종류 선택</option>
      ${CERTIFICATES.map(c => `<option value="${c.name}" ${c.name === certName ? 'selected' : ''}>${c.name}</option>`).join('')}
    </select>
    <select class="cert-grade-select">
      <option value="">급수 선택</option>
    </select>
    <button class="btn-delete-cert" onclick="deleteCertRow(this)" title="삭제">✕</button>
  `;
  certTableBody.appendChild(row);

  const nameSelect = row.querySelector('.cert-name-select');
  const gradeSelect = row.querySelector('.cert-grade-select');

  if (certName) {
    populateGrades(gradeSelect, certName, grade);
  }

  nameSelect.addEventListener('change', () => {
    const selected = nameSelect.value;
    populateGrades(gradeSelect, selected, '');
    nameSelect.classList.remove('error');
    gradeSelect.classList.remove('error');
  });
}

function onCertNameChange(select) {
  const gradeSelect = select.parentElement.querySelector('.cert-grade-select');
  populateGrades(gradeSelect, select.value, '');
  select.classList.remove('error');
  gradeSelect.classList.remove('error');
}

function populateGrades(gradeSelect, certName, selectedGrade) {
  const cert = CERTIFICATES.find(c => c.name === certName);
  gradeSelect.innerHTML = '<option value="">급수 선택</option>';
  if (cert) {
    cert.grades.forEach(g => {
      const opt = document.createElement('option');
      opt.value = g;
      opt.textContent = g;
      if (g === selectedGrade) opt.selected = true;
      gradeSelect.appendChild(opt);
    });
    // 급수가 1개뿐이면 자동 선택
    if (cert.grades.length === 1) {
      gradeSelect.value = cert.grades[0];
    }
  }
}

function deleteCertRow(btn) {
  const row = btn.closest('.cert-row');
  if (certTableBody.children.length <= 1) {
    showToast('자격증 항목은 최소 1개 이상 있어야 합니다.', 'info');
    return;
  }
  row.remove();
}

document.getElementById('btn-add-cert').addEventListener('click', () => addCertRow());

// ── 자격증 데이터 수집 ─────────────────────────────────────────────────

function getCertificates() {
  const certs = [];
  let hasError = false;
  certTableBody.querySelectorAll('.cert-row').forEach(row => {
    const nameSelect = row.querySelector('.cert-name-select');
    const gradeSelect = row.querySelector('.cert-grade-select');
    const name = nameSelect.value;
    const grade = gradeSelect.value;

    if (!name && !grade) return; // 빈 행 무시

    if (name && !grade) {
      gradeSelect.classList.add('error');
      hasError = true;
    } else if (name && grade) {
      nameSelect.classList.remove('error');
      gradeSelect.classList.remove('error');
      certs.push({ name, grade });
    }
  });
  return { certs, hasError };
}

// ── 유효성 검증 (SRS 6.3 프론트엔드 검증) ────────────────────────────────

function validate() {
  let valid = true;
  clearAllErrors();

  // 직렬 미선택 검증 (UC-001 예외 흐름)
  if (!selectedSeries) {
    showError('series-error', '직렬을 선택해 주세요.');
    valid = false;
  }

  // 자격증 급수 누락 검증 (UC-002 예외 흐름)
  const { certs, hasError } = getCertificates();
  if (hasError) {
    showToast('급수를 선택하지 않은 자격증 항목이 있습니다.', 'error');
    valid = false;
  }

  // 토익 점수 범위 검증 (UC-003 예외 흐름)
  const toeicInput = document.getElementById('toeic');
  const toeicVal = toeicInput.value;
  if (toeicVal !== '' && (parseInt(toeicVal) < 0 || parseInt(toeicVal) > 990 || isNaN(parseInt(toeicVal)))) {
    toeicInput.classList.add('error');
    showError('toeic-error', '토익 점수는 0~990 범위여야 합니다.');
    valid = false;
  }

  // 스펙 최소 1개 입력 검증
  const toeicSpeaking = document.getElementById('toeic-speaking').value;
  const opic = document.getElementById('opic').value;
  const hasAnySpec = certs.length > 0 || toeicVal || toeicSpeaking || opic;
  if (!hasAnySpec) {
    showToast('자격증 또는 어학 성적 중 최소 1개 이상 입력해 주세요.', 'error');
    valid = false;
  }

  return { valid, certs };
}

// ── 계산하기 클릭 (UC-004) ───────────────────────────────────────────────

async function onCalculate() {
  const { valid, certs } = validate();
  if (!valid) return;

  // 로딩 스피너 표시 (SRS 5.1 계산하기 버튼 명세)
  setCalculatingState(true);

  const toeicRaw = document.getElementById('toeic').value;
  const toeicSpeaking = document.getElementById('toeic-speaking').value || null;
  const opic = document.getElementById('opic').value || null;

  const specData = {
    job_series: selectedSeries,
    certificates: certs,
    language_scores: {
      toeic: toeicRaw ? parseInt(toeicRaw) : null,
      toeic_speaking: toeicSpeaking,
      opic: opic,
    },
  };

  // 입력값 저장 (스펙 수정하기 복귀 시 사용)
  saveInputState();

  try {
    const result = await API.calculateBonusScore(specData);
    renderResults(result);
  } catch (err) {
    if (err instanceof API.ApiError) {
      if (err.status === 422) {
        showToast(`입력 오류: ${err.message}`, 'error');
      } else if (err.status === 404) {
        showToast('현재 등록된 공기업 데이터가 없습니다.', 'info');
      } else {
        showToast('계산 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.', 'error');
      }
    } else {
      showToast('서버에 연결할 수 없습니다. 백엔드 서버를 확인해 주세요.', 'error');
    }
  } finally {
    setCalculatingState(false);
  }
}

function setCalculatingState(loading) {
  btnCalculate.disabled = loading;
  btnCalculate.innerHTML = loading
    ? `<div class="spinner"></div> 계산 중...`
    : `🔍 가산점 계산하기`;
}

// ── 결과 렌더링 (UC-005) ────────────────────────────────────────────────

function renderResults(data) {
  const { job_series, results } = data;

  if (!results || results.length === 0) {
    showToast('해당 직렬에 매칭되는 공기업 데이터가 없습니다.', 'info');
    return;
  }

  // 요약 통계
  const perfectCount = results.filter(r => r.match_rate >= 100).length;
  const avgRate = results.reduce((s, r) => s + r.match_rate, 0) / results.length;
  summaryTotal.textContent = results.length;
  summaryPerfect.textContent = perfectCount;
  summaryAvg.textContent = avgRate.toFixed(1) + '%';

  // 결과 제목
  resultTitle.textContent = `📊 나의 공기업 가산점 매칭 결과`;
  resultSubtitle.textContent = `${job_series} 기준 · ${results.length}개 기업`;

  // 테이블 렌더링
  resultTableBody.innerHTML = '';
  results.forEach((item, idx) => {
    const rank = idx + 1;
    const isPerfect = item.match_rate >= 100;
    const rateClass = isPerfect ? 'perfect' : item.match_rate >= 80 ? 'high' : item.match_rate >= 60 ? 'mid' : 'low';
    const badgeClass = isPerfect ? 'badge-perfect' : item.match_rate >= 80 ? 'badge-high' : item.match_rate >= 60 ? 'badge-mid' : 'badge-low';
    const rankClass = rank === 1 ? 'top1' : rank === 2 ? 'top2' : rank === 3 ? 'top3' : '';

    // 데이터 행
    const tr = document.createElement('tr');
    tr.dataset.companyId = item.company_id;
    tr.innerHTML = `
      <td class="rank-cell ${rankClass}">${rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : rank}</td>
      <td>
        <div class="font-bold">${escapeHtml(item.company_name)}</div>
      </td>
      <td>
        <span class="font-bold">${item.my_bonus_score}점</span>
        <span class="text-sm text-gray-500"> / ${item.max_bonus_score}점</span>
      </td>
      <td class="match-rate-cell">
        <div class="match-bar-wrap">
          <div class="match-bar-bg">
            <div class="match-bar-fill ${rateClass}" style="width: 0%" data-width="${Math.min(item.match_rate, 100)}%"></div>
          </div>
          <span class="match-rate-pct" style="color: var(--${rateClass === 'perfect' ? 'success' : rateClass === 'high' ? 'primary' : rateClass === 'mid' ? 'warning' : 'danger'})">${item.match_rate}%</span>
        </div>
      </td>
      <td>
        ${isPerfect
          ? `<span class="badge badge-perfect">✅ 만점</span>`
          : `<button class="btn-feedback" onclick="toggleFeedback(this, ${item.company_id})" data-company-id="${item.company_id}">💡 피드백 ▾</button>`
        }
      </td>
    `;
    resultTableBody.appendChild(tr);

    // 피드백 행 (접힌 상태)
    if (!isPerfect && item.feedback) {
      const feedbackTr = document.createElement('tr');
      feedbackTr.className = 'feedback-row hidden';
      feedbackTr.id = `feedback-${item.company_id}`;
      feedbackTr.innerHTML = `
        <td colspan="5">
          <div class="feedback-content">
            <span class="feedback-icon">💡</span>
            <span>${escapeHtml(item.feedback)}</span>
          </div>
        </td>
      `;
      resultTableBody.appendChild(feedbackTr);
    }
  });

  // 결과 화면 전환
  inputSection.style.display = 'none';
  resultSection.style.display = 'block';

  // 매칭률 바 애니메이션
  requestAnimationFrame(() => {
    document.querySelectorAll('.match-bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.width;
    });
  });

  // 스크롤 상단으로
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── 피드백 토글 (UC-006) ────────────────────────────────────────────────

function toggleFeedback(btn, companyId) {
  const feedbackRow = document.getElementById(`feedback-${companyId}`);
  if (!feedbackRow) return;

  const isOpen = !feedbackRow.classList.contains('hidden');
  if (isOpen) {
    feedbackRow.classList.add('hidden');
    btn.classList.remove('open');
    btn.innerHTML = '💡 피드백 ▾';
  } else {
    feedbackRow.classList.remove('hidden');
    btn.classList.add('open');
    btn.innerHTML = '💡 피드백 ▴';
  }
}

// ── 스펙 수정하기 (UC-005 기본 흐름 4) ──────────────────────────────────

function onBack() {
  resultSection.style.display = 'none';
  inputSection.style.display = 'block';
  restoreInputState();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function saveInputState() {
  const toeicVal = document.getElementById('toeic').value;
  const toeicSpeakingVal = document.getElementById('toeic-speaking').value;
  const opicVal = document.getElementById('opic').value;

  const certs = [];
  certTableBody.querySelectorAll('.cert-row').forEach(row => {
    certs.push({
      name: row.querySelector('.cert-name-select').value,
      grade: row.querySelector('.cert-grade-select').value,
    });
  });

  lastInputState = { series: selectedSeries, certs, toeic: toeicVal, toeicSpeaking: toeicSpeakingVal, opic: opicVal };
}

function restoreInputState() {
  if (!lastInputState) return;
  // 직렬 복원 (드롭다운)
  if (lastInputState.series) {
    const seriesSelect = document.getElementById('series-select');
    if (seriesSelect) {
      seriesSelect.value = lastInputState.series;
      seriesSelect.classList.add('selected');
    }
    // 구버전 버튼 방식 (하위 호환)
    document.querySelectorAll('.series-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.series === lastInputState.series);
    });
    selectedSeries = lastInputState.series;
  }
  // 어학 복원
  document.getElementById('toeic').value = lastInputState.toeic || '';
  document.getElementById('toeic-speaking').value = lastInputState.toeicSpeaking || '';
  document.getElementById('opic').value = lastInputState.opic || '';
  // 자격증 복원
  certTableBody.innerHTML = '';
  if (lastInputState.certs.length) {
    lastInputState.certs.forEach(c => addCertRow(c.name, c.grade));
  } else {
    addCertRow();
  }
}

// ── 오류 표시 유틸 ───────────────────────────────────────────────────────

function showError(elementId, msg) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = '⚠ ' + msg; el.style.display = 'flex'; }
}
function clearError(elementId) {
  const el = document.getElementById(elementId);
  if (el) { el.textContent = ''; el.style.display = 'none'; }
}
function clearAllErrors() {
  document.querySelectorAll('.error-msg').forEach(el => { el.textContent = ''; el.style.display = 'none'; });
  document.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
}

// ── Toast 알림 (SRS 5.1 오류 Toast 컴포넌트) ─────────────────────────────

function showToast(message, type = 'info') {
  const icons = { error: '❌', success: '✅', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span class="toast-icon">${icons[type]}</span><span>${escapeHtml(message)}</span>`;
  toastContainer.appendChild(toast);

  // 3초 후 자동 소멸 (SRS 5.1)
  setTimeout(() => {
    toast.classList.add('closing');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── 입력 이벤트 (오류 자동 초기화) ─────────────────────────────────────

document.getElementById('toeic').addEventListener('input', function () {
  this.classList.remove('error');
  clearError('toeic-error');
});

// ── HTML 이스케이프 ──────────────────────────────────────────────────────

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── 전역 노출 (HTML onclick 핸들러) ─────────────────────────────────────

window.toggleFeedback = toggleFeedback;
window.deleteCertRow = deleteCertRow;
window.onCertNameChange = onCertNameChange;
