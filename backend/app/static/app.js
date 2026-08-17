/**
 * AI Resume ATS — Frontend Logic
 * Handles: drag-drop, file selection, API call, results rendering, animations
 */

'use strict';

// ── DOM Refs ────────────────────────────────────────────────────────────────
const dropZone        = document.getElementById('drop-zone');
const resumeInput     = document.getElementById('resume-input');
const dropZoneContent = document.getElementById('drop-zone-content');
const fileSelectedView= document.getElementById('file-selected-view');
const fileNameDisplay = document.getElementById('file-name-display');
const fileSizeDisplay = document.getElementById('file-size-display');
const removeFileBtn   = document.getElementById('remove-file-btn');
const browseLink      = document.getElementById('browse-link');

const jdTextarea      = document.getElementById('jd-textarea');
const charCount       = document.getElementById('char-count');

const analyzeBtn      = document.getElementById('analyze-btn');
const btnIcon         = document.getElementById('btn-icon');
const btnLabel        = document.getElementById('btn-label');
const btnSpinner      = document.getElementById('btn-spinner');

const inputSection    = document.getElementById('input-section');
const resultsSection  = document.getElementById('results-section');

// Score ring
const ringFill        = document.getElementById('ring-fill');
const scoreNumber     = document.getElementById('score-number');
const scoreSvg        = document.getElementById('score-svg');

// Sub-scores
const skillScoreVal   = document.getElementById('skill-score-val');
const semanticScoreVal= document.getElementById('semantic-score-val');
const tfidfScoreVal   = document.getElementById('tfidf-score-val');
const sectionScoreVal = document.getElementById('section-score-val');
const skillProgress   = document.getElementById('skill-progress');
const semanticProgress= document.getElementById('semantic-progress');
const tfidfProgress   = document.getElementById('tfidf-progress');
const sectionProgress = document.getElementById('section-progress');

// Info
const candidateName   = document.getElementById('candidate-name');
const candidateEmail  = document.getElementById('candidate-email');
const matchBadge      = document.getElementById('match-badge');

// Skills
const matchedChips    = document.getElementById('matched-chips');
const missingChips    = document.getElementById('missing-chips');
const matchedCount    = document.getElementById('matched-count');
const missingCount    = document.getElementById('missing-count');

// N-gram table
const ngramTbody      = document.getElementById('ngram-tbody');

// Recommendations
const recList         = document.getElementById('recommendations-list');

// Reanalyze
const reanalyzeBtn    = document.getElementById('reanalyze-btn');

// Toast
const toast           = document.getElementById('toast');
const toastIcon       = document.getElementById('toast-icon');
const toastMsg        = document.getElementById('toast-msg');

// ── State ────────────────────────────────────────────────────────────────────
let selectedFile = null;
const CIRCUMFERENCE = 427; // 2 * π * 68

// ── Inject SVG gradient defs ─────────────────────────────────────────────────
(function injectSvgGradient() {
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%"   stop-color="#7c6aff"/>
      <stop offset="100%" stop-color="#00d4ff"/>
    </linearGradient>`;
  scoreSvg.prepend(defs);
})();

// ── File Selection ────────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function setFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('⚠️', 'Only PDF files are supported. Please select a .pdf file.');
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showToast('⚠️', 'File size exceeds 5 MB. Please upload a smaller PDF.');
    return;
  }
  selectedFile = file;
  fileNameDisplay.textContent = file.name;
  fileSizeDisplay.textContent = formatBytes(file.size);
  dropZoneContent.classList.add('hidden');
  fileSelectedView.classList.remove('hidden');
}

function clearFile() {
  selectedFile = null;
  resumeInput.value = '';
  dropZoneContent.classList.remove('hidden');
  fileSelectedView.classList.add('hidden');
}

// ── Drop Zone Events ──────────────────────────────────────────────────────────
dropZone.addEventListener('click', (e) => {
  if (e.target === removeFileBtn || removeFileBtn.contains(e.target)) return;
  resumeInput.click();
});
dropZone.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); resumeInput.click(); }
});
browseLink.addEventListener('click', (e) => { e.stopPropagation(); resumeInput.click(); });

resumeInput.addEventListener('change', () => {
  if (resumeInput.files.length > 0) setFile(resumeInput.files[0]);
});
removeFileBtn.addEventListener('click', (e) => { e.stopPropagation(); clearFile(); });

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('dragover'); });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
});

// ── Character Count ───────────────────────────────────────────────────────────
jdTextarea.addEventListener('input', () => {
  const len = jdTextarea.value.length;
  charCount.textContent = `${len.toLocaleString()} character${len !== 1 ? 's' : ''}`;
});

// ── Analyze Button ────────────────────────────────────────────────────────────
analyzeBtn.addEventListener('click', handleAnalyze);

async function handleAnalyze() {
  if (!selectedFile) {
    showToast('📄', 'Please upload your resume PDF first.');
    return;
  }
  const jd = jdTextarea.value.trim();
  if (!jd) {
    showToast('📝', 'Please paste a job description before analyzing.');
    jdTextarea.focus();
    return;
  }
  if (jd.length < 50) {
    showToast('📝', 'Job description seems too short. Paste the full JD for accurate results.');
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append('resume_file', selectedFile);
    formData.append('jd_text', jd);

    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errMsg = data.detail || `Server error ${response.status}`;
      showToast('❌', errMsg);
      return;
    }

    renderResults(data);

  } catch (err) {
    console.error(err);
    showToast('🔌', 'Could not connect to the analysis server. Make sure the backend is running.');
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  analyzeBtn.disabled = on;
  if (on) {
    btnIcon.classList.add('hidden');
    btnLabel.textContent = 'Analyzing…';
    btnSpinner.classList.remove('hidden');
  } else {
    btnIcon.classList.remove('hidden');
    btnLabel.textContent = 'Analyze Resume';
    btnSpinner.classList.add('hidden');
  }
}

// ── Results Rendering ─────────────────────────────────────────────────────────
function renderResults(data) {
  // Candidate info
  candidateName.textContent  = data.candidate_name || '—';
  candidateEmail.textContent = data.email !== 'Not Found' ? data.email : '—';

  // Match badge
  const ml = (data.match_level || '').toLowerCase().replace(' ', '-');
  matchBadge.textContent = data.match_level || '—';
  matchBadge.className = `match-badge badge-${ml}`;

  // Score ring animation
  animateScore(data.ats_score || 0);

  // Sub-score bars (animate after brief delay for cascade effect)
  setTimeout(() => animateSubScore(skillScoreVal,    skillProgress,    data.skill_match_score || 0),  200);
  setTimeout(() => animateSubScore(semanticScoreVal, semanticProgress, data.semantic_score || 0),     350);
  setTimeout(() => animateSubScore(tfidfScoreVal,    tfidfProgress,    Math.max(data.tfidf_score || 0, data.ngram_score || 0)), 500);
  setTimeout(() => animateSubScore(sectionScoreVal,  sectionProgress,  data.section_score || 0),      650);

  // Skills chips
  renderChips(matchedChips, data.matched_skills || [], 'chip-matched');
  renderChips(missingChips,  data.missing_skills  || [], 'chip-missing');
  matchedCount.textContent = (data.matched_skills || []).length;
  missingCount.textContent = (data.missing_skills || []).length;

  // N-gram table
  renderNgramTable(data);

  // Recommendations
  renderRecommendations(data.recommendations || []);

  // Show results, hide input
  inputSection.classList.add('hidden');
  resultsSection.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function animateScore(targetScore) {
  const offset = CIRCUMFERENCE - (targetScore / 100) * CIRCUMFERENCE;
  // small delay to let the DOM paint
  requestAnimationFrame(() => {
    setTimeout(() => { ringFill.style.strokeDashoffset = offset; }, 50);
  });

  // Counter animation
  let current = 0;
  const duration = 1200;
  const step = duration / targetScore;
  const timer = setInterval(() => {
    current = Math.min(current + 1, targetScore);
    scoreNumber.textContent = current;
    if (current >= targetScore) clearInterval(timer);
  }, step);
}

function animateSubScore(labelEl, barEl, score) {
  labelEl.textContent = `${Math.round(score)}%`;
  barEl.style.width   = `${Math.min(100, score)}%`;
}

function renderChips(container, skills, chipClass) {
  container.innerHTML = '';
  if (!skills.length) {
    container.innerHTML = `<span class="empty-chips">None found</span>`;
    return;
  }
  skills.forEach(skill => {
    const chip = document.createElement('span');
    chip.className = `skill-chip ${chipClass}`;
    chip.textContent = skill;
    container.appendChild(chip);
  });
}

function renderNgramTable(data) {
  const breakdown = data.ngram_breakdown || {};
  const rows = [
    { model: 'TF-IDF (Unigram)',          score: data.tfidf_score    || 0, weight: '—' },
    { model: 'N-Gram Unigram',            score: breakdown.unigram_score || 0, weight: '—' },
    { model: 'N-Gram Bigram',             score: breakdown.bigram_score  || 0, weight: '—' },
    { model: 'N-Gram Trigram',            score: breakdown.trigram_score || 0, weight: '—' },
    { model: 'Semantic Embedding (MiniLM)',score: data.semantic_score  || 0, weight: '35%' },
    { model: 'Skill Match',               score: data.skill_match_score || 0, weight: '40%' },
    { model: 'Section Structure',         score: data.section_score  || 0, weight: '10%' },
  ];

  ngramTbody.innerHTML = rows.map(row => `
    <tr>
      <td class="table-model">${row.model}</td>
      <td class="table-score">${row.score.toFixed(1)}%</td>
      <td>
        <div class="table-bar-track">
          <div class="table-bar-fill" style="width: ${Math.min(100, row.score)}%"></div>
        </div>
      </td>
      <td class="table-weight">${row.weight}</td>
    </tr>
  `).join('');
}

function renderRecommendations(recs) {
  recList.innerHTML = '';
  if (!recs.length) {
    recList.innerHTML = `<p class="no-recs">🎉 Great! Your resume looks well-optimized for this job description.</p>`;
    return;
  }
  recs.forEach((rec, i) => {
    const item = document.createElement('div');
    item.className = 'rec-item';
    item.innerHTML = `
      <span class="rec-num">${i + 1}</span>
      <p class="rec-text">${rec}</p>`;
    recList.appendChild(item);
  });
}

// ── Re-analyze ────────────────────────────────────────────────────────────────
reanalyzeBtn.addEventListener('click', () => {
  resultsSection.classList.add('hidden');
  inputSection.classList.remove('hidden');
  // Reset ring
  ringFill.style.strokeDashoffset = CIRCUMFERENCE;
  scoreNumber.textContent = '0';
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Toast ─────────────────────────────────────────────────────────────────────
let toastTimer = null;
function showToast(icon, msg, duration = 4500) {
  toastIcon.textContent = icon;
  toastMsg.textContent  = msg;
  toast.classList.remove('hidden');
  // Force reflow before adding .show
  void toast.offsetHeight;
  toast.classList.add('show');

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.classList.add('hidden'), 350);
  }, duration);
}
