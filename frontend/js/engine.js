/**
 * 가산점 룰 엔진 (JavaScript 이식판)
 * Python backend/app/engine/rule_engine.py 와 동일한 로직
 *
 * 지원 룰:
 *   1. OR 룰: 동일 category 자격증 중 최고 score 1개만 반영
 *   2. PROPORTIONAL 어학 비례 연산: (유저점수 / base_score) × score
 *   3. 합산 한도(Cap): max_bonus_score 초과분 절삭
 *   4. 매칭률: (내 가산점 / max_bonus_score) × 100
 *   5. 피드백 멘트 생성 (100% 미만 기업 대상)
 */

// ── 어학 등급 순서 ────────────────────────────────────────────────────────

const TOEIC_SPEAKING_ORDER = ["Lv.1","Lv.2","Lv.3","Lv.4","Lv.5","Lv.6","Lv.7","Lv.8"];
const OPIC_ORDER = ["NL","IL","IM1","IM2","IM3","IH","AL"];

// ── 내부 유틸 함수 ────────────────────────────────────────────────────────

function _calcProportional(userScore, baseScore, ruleScore) {
  if (baseScore <= 0) return 0;
  return Math.round((userScore / baseScore) * ruleScore * 100) / 100;
}

function _isLanguageRule(rule) {
  const upper = rule.certificateName.toUpperCase().replace(/\s/g, "");
  return ["TOEIC","토익","OPIC","오픽","SPEAKING","스피킹","어학"].some(
    kw => upper.includes(kw.toUpperCase())
  );
}

function _matchLanguageRule(rule, lang) {
  const certUpper = rule.certificateName.toUpperCase().replace(/\s/g, "");

  // TOEIC (토익) — PROPORTIONAL
  if (certUpper.includes("TOEIC") && !certUpper.includes("SPEAKING") && !certUpper.includes("스피킹")) {
    if (lang.toeic != null && lang.toeic > 0) {
      if (rule.calcType === "PROPORTIONAL" && rule.baseScore) {
        return _calcProportional(lang.toeic, rule.baseScore, rule.score);
      } else {
        // FIXED: 특정 점수 이상이면 고정 가산점
        const threshold = parseInt(rule.grade.replace(/[^0-9]/g, ""));
        if (!isNaN(threshold) && lang.toeic >= threshold) return rule.score;
      }
    }
    return null;
  }

  // 토익스피킹
  if (certUpper.includes("SPEAKING") || certUpper.includes("스피킹")) {
    if (lang.toeicSpeaking) {
      const userIdx = TOEIC_SPEAKING_ORDER.indexOf(lang.toeicSpeaking);
      const ruleIdx = TOEIC_SPEAKING_ORDER.indexOf(rule.grade);
      if (ruleIdx >= 0 && userIdx >= ruleIdx) {
        if (rule.calcType === "PROPORTIONAL" && rule.baseScore) {
          return _calcProportional(userIdx + 1, rule.baseScore, rule.score);
        }
        return rule.score;
      }
    }
    return null;
  }

  // OPIc
  if (certUpper.includes("OPIC") || certUpper.includes("오픽")) {
    if (lang.opic) {
      const userIdx = OPIC_ORDER.indexOf(lang.opic);
      const ruleIdx = OPIC_ORDER.indexOf(rule.grade);
      if (ruleIdx >= 0 && userIdx >= ruleIdx) {
        if (rule.calcType === "PROPORTIONAL" && rule.baseScore) {
          return _calcProportional(userIdx + 1, rule.baseScore, rule.score);
        }
        return rule.score;
      }
    }
    return null;
  }

  return null;
}

// ── 피드백 생성 ───────────────────────────────────────────────────────────

function _generateFeedback(company, certificates, languageScores, myScore) {
  const shortage = company.maxBonusScore - myScore;
  const tips = [];

  // 자격증 룰 피드백
  const certRulesByCategory = {};
  const langRules = [];
  for (const rule of company.rules) {
    if (_isLanguageRule(rule)) {
      langRules.push(rule);
    } else {
      if (!certRulesByCategory[rule.category]) certRulesByCategory[rule.category] = [];
      certRulesByCategory[rule.category].push(rule);
    }
  }

  for (const [, catRules] of Object.entries(certRulesByCategory)) {
    let currentBest = 0;
    for (const rule of catRules) {
      for (const cert of certificates) {
        if (rule.certificateName.trim() === cert.name.trim() &&
            rule.grade.trim() === cert.grade.trim()) {
          if (rule.score > currentBest) currentBest = rule.score;
        }
      }
    }
    const possibleMax = Math.max(...catRules.map(r => r.score));
    const gain = possibleMax - currentBest;
    if (gain > 0) {
      const bestRule = catRules.reduce((a, b) => a.score >= b.score ? a : b);
      tips.push(`'${bestRule.certificateName}(${bestRule.grade})' 취득 시 +${gain.toFixed(1)}점 추가 가능`);
    }
  }

  // 어학 피드백
  if (langRules.length > 0) {
    const toeicPropRule = langRules.find(r =>
      r.certificateName.toUpperCase().includes("TOEIC") &&
      !r.certificateName.toUpperCase().includes("SPEAKING") &&
      r.calcType === "PROPORTIONAL"
    );
    if (toeicPropRule && toeicPropRule.baseScore) {
      const currentToeic = languageScores.toeic || 0;
      const maxLangScore = toeicPropRule.score;
      const currentLangScore = _calcProportional(currentToeic, toeicPropRule.baseScore, maxLangScore);
      if (currentLangScore < maxLangScore) {
        const gain = Math.round((maxLangScore - currentLangScore) * 10) / 10;
        tips.push(`토익 ${toeicPropRule.baseScore}점 달성 시 어학 가산점 +${gain}점 추가 가능`);
      }
    }
  }

  if (tips.length === 0) {
    tips.push(`${company.name} 만점까지 ${shortage.toFixed(1)}점 부족합니다.`);
  }

  return tips.slice(0, 2).join(" / ") + ` (부족: ${shortage.toFixed(1)}점)`;
}

// ── 단일 기업 계산 ────────────────────────────────────────────────────────

function calculateCompanyScore(company, certificates, languageScores) {
  const rules = company.rules;
  let totalScore = 0;

  // STEP 1: 자격증 룰 (OR 룰)
  const certRulesByCategory = {};
  const langRules = [];

  for (const rule of rules) {
    if (_isLanguageRule(rule)) {
      langRules.push(rule);
    } else {
      if (!certRulesByCategory[rule.category]) certRulesByCategory[rule.category] = [];
      certRulesByCategory[rule.category].push(rule);
    }
  }

  for (const [, catRules] of Object.entries(certRulesByCategory)) {
    let bestScore = null;
    for (const rule of catRules) {
      for (const cert of certificates) {
        if (rule.certificateName.trim() === cert.name.trim() &&
            rule.grade.trim() === cert.grade.trim()) {
          if (bestScore === null || rule.score > bestScore) {
            bestScore = rule.score;
          }
        }
      }
    }
    if (bestScore !== null) totalScore += bestScore;
  }

  // STEP 2: 어학 룰 (category별 OR 룰)
  const langByCategory = {};
  for (const rule of langRules) {
    if (!langByCategory[rule.category]) langByCategory[rule.category] = [];
    langByCategory[rule.category].push(rule);
  }

  for (const [, lRules] of Object.entries(langByCategory)) {
    let bestLangScore = null;
    for (const rule of lRules) {
      const score = _matchLanguageRule(rule, languageScores);
      if (score !== null) {
        if (bestLangScore === null || score > bestLangScore) bestLangScore = score;
      }
    }
    if (bestLangScore !== null) totalScore += bestLangScore;
  }

  // STEP 3: Cap 적용
  const myBonusScore = Math.round(Math.min(totalScore, company.maxBonusScore) * 100) / 100;

  // STEP 4: 매칭률
  const matchRate = company.maxBonusScore > 0
    ? Math.round((myBonusScore / company.maxBonusScore) * 1000) / 10
    : 0;

  // STEP 5: 피드백
  const feedback = matchRate < 100
    ? _generateFeedback(company, certificates, languageScores, myBonusScore)
    : null;

  return {
    companyId: company.id,
    companyName: company.name,
    myBonusScore,
    maxBonusScore: company.maxBonusScore,
    matchRate,
    feedback,
  };
}

// ── 전체 엔진 실행 ────────────────────────────────────────────────────────

function runEngine(jobSeries, certificates, languageScores) {
  // 해당 직렬 활성 기업 필터
  const targetCompanies = COMPANIES_DATA.filter(c =>
    c.isActive && (c.seriesType === "공통" || c.seriesType === jobSeries)
  );

  const results = [];

  for (const company of targetCompanies) {
    // 해당 기업 룰 (직렬 필터 적용)
    const rules = BONUS_RULES_DATA.filter(rule =>
      rule.companyId === company.id &&
      (rule.seriesFilter === "공통" || rule.seriesFilter === jobSeries)
    );

    try {
      const result = calculateCompanyScore({ ...company, rules }, certificates, languageScores);
      results.push(result);
    } catch (e) {
      console.error(`[Engine] 기업 ID=${company.id} 계산 오류:`, e);
    }
  }

  // 매칭률 내림차순 정렬
  results.sort((a, b) => b.matchRate - a.matchRate);
  return results;
}

// ── 전역 노출 ─────────────────────────────────────────────────────────────
window.Engine = { runEngine };
