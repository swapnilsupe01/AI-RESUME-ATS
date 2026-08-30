/**
 * RESUME_INTEL — Cyber-Intelligence System Frontend Engine
 * Controls: 3D Three.js Particle Network, Tabs, File Upload, API Analytics, and Evidence Verifier
 */

'use strict';

// ── Three.js 3D Particle Network Background ─────────────────────────────────
(function initThreeJsBackground() {
  const container = document.getElementById('threejs-canvas-container');
  if (!container || typeof THREE === 'undefined') return;

  const width = window.innerWidth;
  const height = window.innerHeight;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
  const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  container.appendChild(renderer.domElement);

  // Digital particle grid
  const particlesCount = 1800;
  const positions = new Float32Array(particlesCount * 3);
  const colors = new Float32Array(particlesCount * 3);

  for (let i = 0; i < particlesCount * 3; i += 3) {
    positions[i]     = (Math.random() - 0.5) * 12;
    positions[i + 1] = (Math.random() - 0.5) * 12;
    positions[i + 2] = (Math.random() - 0.5) * 12;

    // Cyber blue to emerald gradient
    colors[i]     = 0.2 + Math.random() * 0.2; // R
    colors[i + 1] = 0.5 + Math.random() * 0.4; // G
    colors[i + 2] = 0.8 + Math.random() * 0.2; // B
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.018,
    vertexColors: true,
    transparent: true,
    opacity: 0.5,
    blending: THREE.AdditiveBlending
  });

  const points = new THREE.Points(geometry, material);
  scene.add(points);
  camera.position.z = 3.5;

  let mouseX = 0;
  let mouseY = 0;

  window.addEventListener('mousemove', (e) => {
    mouseX = (e.clientX / window.innerWidth - 0.5) * 0.4;
    mouseY = (e.clientY / window.innerHeight - 0.5) * 0.4;
  });

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  function animate() {
    requestAnimationFrame(animate);
    points.rotation.y += 0.0008;
    points.rotation.x += 0.0004;

    camera.position.x += (mouseX - camera.position.x) * 0.04;
    camera.position.y += (-mouseY - camera.position.y) * 0.04;
    camera.lookAt(scene.position);

    renderer.render(scene, camera);
  }

  animate();
})();

// ── DOM Element References ──────────────────────────────────────────────────
const dropZone          = document.getElementById('drop-zone');
const resumeInput       = document.getElementById('resume-input');
const dropZoneContent   = document.getElementById('drop-zone-content');
const fileSelectedView  = document.getElementById('file-selected-view');
const fileNameDisplay   = document.getElementById('file-name-display');
const fileSizeDisplay   = document.getElementById('file-size-display');
const removeFileBtn     = document.getElementById('remove-file-btn');
const browseLink        = document.getElementById('browse-link');

const linksToggle       = document.getElementById('links-toggle');
const toggleArrow       = document.getElementById('toggle-arrow');
const optionalLinksBody = document.getElementById('optional-links-body');
const githubOverride    = document.getElementById('github-override');
const portfolioOverride = document.getElementById('portfolio-override');

const jdTextarea        = document.getElementById('jd-textarea');
const charCount         = document.getElementById('char-count');
const loadSampleBtn     = document.getElementById('load-sample-btn');

const analyzeBtn        = document.getElementById('analyze-btn');
const btnIcon           = document.getElementById('btn-icon');
const btnLabel          = document.getElementById('btn-label');
const btnSpinner        = document.getElementById('btn-spinner');

const inputSection      = document.getElementById('input-section');
const resultsSection    = document.getElementById('results-section');

// Profile & Scores
const candidateName     = document.getElementById('candidate-name');
const candidateContact  = document.getElementById('candidate-contact');
const overallProfileVal = document.getElementById('overall-profile-score');

// Gauges
const jobRingFill       = document.getElementById('job-ring-fill');
const jobScoreNum       = document.getElementById('job-score-num');
const jobMatchBadge     = document.getElementById('job-match-badge');

const evidenceRingFill  = document.getElementById('evidence-ring-fill');
const evidenceScoreNum  = document.getElementById('evidence-score-num');
const evidenceBadge     = document.getElementById('evidence-badge');

// Sub-Metrics
const subSkillVal       = document.getElementById('sub-skill-val');
const subSkillBar       = document.getElementById('sub-skill-bar');
const subEmbVal         = document.getElementById('sub-emb-val');
const subEmbBar         = document.getElementById('sub-emb-bar');
const subTfidfVal       = document.getElementById('sub-tfidf-val');
const subTfidfBar       = document.getElementById('sub-tfidf-bar');
const subGhVal          = document.getElementById('sub-gh-val');
const subGhBar          = document.getElementById('sub-gh-bar');

// Evidence Section
const pillVerified      = document.getElementById('pill-verified');
const pillPartial       = document.getElementById('pill-partial');
const pillUnsupported   = document.getElementById('pill-unsupported');
const reposContainer    = document.getElementById('repos-preview-container');
const claimsTbody       = document.getElementById('claims-tbody');

// Inconsistency
const inconsistencyAlert   = document.getElementById('inconsistency-alert');
const inconsistencyMessage = document.getElementById('inconsistency-message');

// Skills
const matchedChips      = document.getElementById('matched-chips');
const missingChips      = document.getElementById('missing-chips');
const matchedCount      = document.getElementById('matched-count');
const missingCount      = document.getElementById('missing-count');

// Recommendations
const recsList          = document.getElementById('recommendations-list');
const reanalyzeBtn      = document.getElementById('reanalyze-btn');

// Standalone Project Verifier
const directRepoUrl     = document.getElementById('direct-repo-url');
const directProjectName = document.getElementById('direct-project-name');
const directClaimsTech  = document.getElementById('direct-claims-tech');
const directVerifyBtn   = document.getElementById('direct-verify-btn');
const directResultsBox  = document.getElementById('direct-results-container');
const directResultsJson = document.getElementById('direct-results-json');

// Toast
const toast             = document.getElementById('toast');
const toastIcon         = document.getElementById('toast-icon');
const toastMsg          = document.getElementById('toast-msg');

// ── State ────────────────────────────────────────────────────────────────────
let selectedFile = null;
let currentReportData = null;
const CIRCUMFERENCE = 427; // 2 * PI * 68

// ── Tab Switching ────────────────────────────────────────────────────────────
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active', 'text-primary', 'border-b-2', 'border-primary'));
    document.querySelectorAll('.view-content').forEach(v => v.classList.add('hidden'));

    tab.classList.add('active');
    const targetId = tab.getAttribute('data-target');
    const targetView = document.getElementById(targetId);
    if (targetView) targetView.classList.remove('hidden');
  });
});

// ── File Management ──────────────────────────────────────────────────────────
function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function setFile(file) {
  if (!file) return;
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    showToast('error', 'Only PDF files are supported. Please select a .pdf file.');
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

dropZone.addEventListener('click', (e) => {
  if (e.target === removeFileBtn || removeFileBtn.contains(e.target)) return;
  resumeInput.click();
});
browseLink.addEventListener('click', (e) => { e.stopPropagation(); resumeInput.click(); });
resumeInput.addEventListener('change', () => {
  if (resumeInput.files.length > 0) setFile(resumeInput.files[0]);
});
removeFileBtn.addEventListener('click', (e) => { e.stopPropagation(); clearFile(); });

dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-primary'); });
dropZone.addEventListener('dragleave', () => { dropZone.classList.remove('border-primary'); });
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('border-primary');
  if (e.dataTransfer.files.length > 0) setFile(e.dataTransfer.files[0]);
});

// Optional Links Accordion
linksToggle.addEventListener('click', () => {
  optionalLinksBody.classList.toggle('hidden');
  toggleArrow.textContent = optionalLinksBody.classList.contains('hidden') ? 'expand_more' : 'expand_less';
});

// Character Counter
jdTextarea.addEventListener('input', () => {
  const len = jdTextarea.value.length;
  charCount.textContent = `${len.toLocaleString()} chars`;
});

// Load Demo Sample Preset
loadSampleBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/sample-data');
    if (res.ok) {
      const data = await res.json();
      jdTextarea.value = data.sample_jd;
      charCount.textContent = `${data.sample_jd.length.toLocaleString()} chars`;
      githubOverride.value = data.sample_github_repo;
      optionalLinksBody.classList.remove('hidden');
      toggleArrow.textContent = 'expand_less';
      showToast('play_arrow', 'Demo ML Engineer JD & GitHub repository loaded! Now select your resume PDF.');
    }
  } catch (err) {
    showToast('error', 'Could not load demo sample.');
  }
});

// ── Analyze Resume & Verify Public Evidence ──────────────────────────────────
analyzeBtn.addEventListener('click', handleAnalyze);

async function handleAnalyze() {
  if (!selectedFile) {
    showToast('upload_file', 'Please select or drop your resume PDF first.');
    return;
  }
  const jd = jdTextarea.value.trim();
  if (!jd) {
    showToast('description', 'Please paste the target Job Description before analyzing.');
    jdTextarea.focus();
    return;
  }

  setLoading(true);

  try {
    const formData = new FormData();
    formData.append('resume_file', selectedFile);
    formData.append('jd_text', jd);

    if (githubOverride.value.trim()) {
      formData.append('github_url', githubOverride.value.trim());
    }
    if (portfolioOverride.value.trim()) {
      formData.append('portfolio_url', portfolioOverride.value.trim());
    }

    const response = await fetch('/api/analyze', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      const errMsg = data.detail || `Server error: ${response.status}`;
      showToast('error', errMsg);
      return;
    }

    currentReportData = data;
    renderResults(data);

  } catch (err) {
    console.error(err);
    showToast('signal_wifi_off', 'Could not connect to the backend server. Ensure FastAPI is running.');
  } finally {
    setLoading(false);
  }
}

function setLoading(on) {
  analyzeBtn.disabled = on;
  if (on) {
    btnIcon.classList.add('hidden');
    btnLabel.textContent = 'ANALYZING & VERIFYING EVIDENCE…';
    btnSpinner.classList.remove('hidden');
  } else {
    btnIcon.classList.remove('hidden');
    btnLabel.textContent = 'ANALYZE RESUME & VERIFY EVIDENCE';
    btnSpinner.classList.add('hidden');
  }
}

// ── Results Rendering ─────────────────────────────────────────────────────────
function renderResults(data) {
  // Candidate Information
  candidateName.textContent = data.candidate_name || 'Candidate';
  const email = data.email !== 'Not Found' ? data.email : 'Email not listed';
  const phone = data.phone !== 'Not Found' ? data.phone : 'Phone not listed';
  candidateContact.textContent = `${email} • ${phone}`;

  // Overall Score
  const overall = data.overall_profile_score || 0;
  overallProfileVal.textContent = `${overall}%`;

  // Dual Gauges
  const jobScore = data.job_match?.score || 0;
  const evScore  = data.project_evidence?.score || 0;

  animateRing(jobRingFill, jobScoreNum, jobScore);
  animateRing(evidenceRingFill, evidenceScoreNum, evScore);

  jobMatchBadge.textContent = data.job_match?.match_level || 'Evaluated';
  evidenceBadge.textContent = data.project_evidence?.evidence_level || 'No Evidence';

  // Sub-Metrics Progress Bars
  const jm = data.job_match || {};
  const pe = data.project_evidence || {};

  setTimeout(() => {
    animateBar(subSkillVal, subSkillBar, jm.semantic_skill_score || 0);
    animateBar(subEmbVal,   subEmbBar,   jm.document_semantic_score || 0);
    animateBar(subTfidfVal, subTfidfBar, Math.max(jm.tfidf_score || 0, jm.ngram_score || 0));
    animateBar(subGhVal,    subGhBar,    pe.github_score || 0);
  }, 250);

  // Inconsistency Callout Alert
  const inconsistencies = pe.inconsistencies || [];
  if (inconsistencies.length > 0) {
    inconsistencyAlert.classList.remove('hidden');
    inconsistencyMessage.innerHTML = inconsistencies.map(inc => 
      `<strong>${inc.project_title} (${inc.repo_name}):</strong> ${inc.message}`
    ).join('<br><br>');
  } else {
    inconsistencyAlert.classList.add('hidden');
  }

  // Evidence Verification Summary
  pillVerified.textContent    = `${pe.verified_claims_count || 0} Verified`;
  pillPartial.textContent     = `${pe.partial_claims_count || 0} Partial`;
  pillUnsupported.textContent = `${pe.unsupported_claims_count || 0} Unsupported`;

  // Render Repositories Preview
  renderRepositories(pe.github_repositories || []);

  // Render Claims Verification Table
  renderClaimsTable(pe.project_reports || []);

  // Skills Chips
  renderSkillsChips(matchedChips, jm.matched_skills || [], 'chip-matched');
  renderSkillsChips(missingChips, jm.missing_skills || [], 'chip-missing');
  matchedCount.textContent = (jm.matched_skills || []).length;
  missingCount.textContent = (jm.missing_skills || []).length;

  // Recommendations
  renderRecommendations('all');

  // Toggle View
  inputSection.classList.add('hidden');
  resultsSection.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function animateRing(ringEl, numEl, targetScore) {
  const offset = CIRCUMFERENCE - (targetScore / 100) * CIRCUMFERENCE;
  ringEl.style.strokeDashoffset = offset;

  let current = 0;
  const duration = 1000;
  const step = targetScore > 0 ? duration / targetScore : 10;
  const timer = setInterval(() => {
    current = Math.min(current + 1, targetScore);
    numEl.textContent = current;
    if (current >= targetScore) clearInterval(timer);
  }, step);
}

function animateBar(labelEl, barEl, score) {
  const rounded = Math.round(score);
  labelEl.textContent = `${rounded}%`;
  barEl.style.width   = `${Math.min(100, rounded)}%`;
}

function renderRepositories(repos) {
  reposContainer.innerHTML = '';
  if (!repos.length) {
    reposContainer.innerHTML = `
      <div class="col-span-full p-4 rounded-lg bg-surface-container-lowest/60 border border-outline-variant/30 text-xs text-outline">
        No public GitHub repositories explicitly found in resume. Add a GitHub link to verify technical claims against code metadata.
      </div>`;
    return;
  }

  repos.forEach(r => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-lg bg-surface-container-lowest/70 border border-outline-variant/40 hover:border-primary/50 transition-all';
    const techTags = (r.technologies || []).slice(0, 5).map(t => 
      `<span class="px-2 py-0.5 rounded text-[11px] font-code-sm bg-surface-container text-on-surface-variant border border-outline-variant/30">${t}</span>`
    ).join(' ');

    card.innerHTML = `
      <div class="flex items-center gap-2 text-xs font-bold text-primary mb-1">
        <span class="material-symbols-outlined text-[16px]">folder_code</span>
        <span>${r.full_name || r.repo_name}</span>
      </div>
      <p class="text-xs text-on-surface-variant line-clamp-2 mb-3">${r.description || 'Public GitHub repository'}</p>
      <div class="flex flex-wrap gap-1.5">${techTags}</div>
    `;
    reposContainer.appendChild(card);
  });
}

function renderClaimsTable(projectReports) {
  claimsTbody.innerHTML = '';
  let allClaims = [];
  projectReports.forEach(proj => {
    (proj.claims_breakdown || []).forEach(claim => {
      allClaims.push({ ...claim, project_title: proj.project_title });
    });
  });

  if (!allClaims.length) {
    claimsTbody.innerHTML = `<tr><td colspan="5" class="p-6 text-center text-outline">No discrete technical claims extracted for verification.</td></tr>`;
    return;
  }

  claimsTbody.innerHTML = allClaims.map(c => `
    <tr class="hover:bg-surface-container/30 transition-colors">
      <td class="p-3">
        <span class="font-semibold text-on-surface">${c.claim}</span>
        <div class="text-[10px] font-code-sm text-outline mt-0.5">Project: ${c.project_title}</div>
      </td>
      <td class="p-3"><span class="px-2 py-0.5 rounded font-code-sm text-[11px] bg-surface-container border border-outline-variant/30 text-on-surface-variant">${c.claim_type}</span></td>
      <td class="p-3 font-code-sm text-[11px] text-on-surface-variant max-w-xs truncate" title="${c.evidence_snippet}">${c.evidence_snippet}</td>
      <td class="p-3 font-code-sm font-bold text-primary">${Math.round(c.similarity_score)}%</td>
      <td class="p-3">
        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-code-sm font-bold ${
          c.badge === 'verified' ? 'status-pill-verified' : (c.badge === 'partial' ? 'status-pill-partial' : 'status-pill-unsupported')
        }">
          ${c.badge === 'verified' ? '🟢 Verified' : (c.badge === 'partial' ? '🟡 Partial' : '🔴 Not Supported')}
        </span>
      </td>
    </tr>
  `).join('');
}

function renderSkillsChips(container, skills, chipType) {
  container.innerHTML = '';
  if (!skills.length) {
    container.innerHTML = `<span class="text-xs text-outline font-code-sm">None detected</span>`;
    return;
  }
  skills.forEach(skill => {
    const chip = document.createElement('span');
    chip.className = chipType === 'chip-matched'
      ? 'px-3 py-1 rounded-full text-xs font-semibold bg-tertiary/10 border border-tertiary/30 text-tertiary flex items-center gap-1.5'
      : 'px-3 py-1 rounded-full text-xs font-semibold bg-error/10 border border-error/30 text-error flex items-center gap-1.5';
    chip.innerHTML = `<span class="material-symbols-outlined text-[14px]">${chipType === 'chip-matched' ? 'check' : 'close'}</span>${skill}`;
    container.appendChild(chip);
  });
}

function renderRecommendations(filter) {
  if (!currentReportData) return;
  recsList.innerHTML = '';

  let list = [];
  if (filter === 'job') {
    list = currentReportData.job_recommendations || [];
  } else if (filter === 'evidence') {
    list = currentReportData.evidence_recommendations || [];
  } else {
    list = currentReportData.recommendations || [];
  }

  if (!list.length) {
    recsList.innerHTML = `<p class="text-xs text-tertiary p-3">🎉 Everything looks exceptionally aligned!</p>`;
    return;
  }

  list.forEach((rec, i) => {
    const item = document.createElement('div');
    item.className = 'flex items-start gap-3 p-3 rounded-lg bg-surface-container-lowest/60 border border-outline-variant/30 text-xs text-on-surface-variant leading-relaxed';
    item.innerHTML = `
      <span class="w-5 h-5 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center flex-shrink-0 text-[11px]">${i + 1}</span>
      <p class="flex-1">${rec}</p>
    `;
    recsList.appendChild(item);
  });
}

// Recommendation filter tabs
document.querySelectorAll('.rec-tab').forEach(tab => {
  tab.addEventListener('click', (e) => {
    document.querySelectorAll('.rec-tab').forEach(t => {
      t.classList.remove('active', 'bg-primary-container', 'text-on-primary-container');
      t.classList.add('bg-surface-container', 'text-on-surface-variant');
    });
    tab.classList.add('active', 'bg-primary-container', 'text-on-primary-container');
    tab.classList.remove('bg-surface-container', 'text-on-surface-variant');
    renderRecommendations(tab.getAttribute('data-filter'));
  });
});

// Re-analyze
reanalyzeBtn.addEventListener('click', () => {
  resultsSection.classList.add('hidden');
  inputSection.classList.remove('hidden');
  jobRingFill.style.strokeDashoffset = CIRCUMFERENCE;
  evidenceRingFill.style.strokeDashoffset = CIRCUMFERENCE;
  jobScoreNum.textContent = '0';
  evidenceScoreNum.textContent = '0';
  overallProfileVal.textContent = '0%';
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ── Standalone Project Verifier ──────────────────────────────────────────────
directVerifyBtn.addEventListener('click', async () => {
  const url = directRepoUrl.value.trim();
  const name = directProjectName.value.trim();
  const tech = directClaimsTech.value.trim();

  if (!url || !tech) {
    showToast('error', 'Please provide a valid GitHub repo URL and claimed technologies.');
    return;
  }

  directVerifyBtn.disabled = true;
  directVerifyBtn.innerHTML = `<span class="btn-spinner"></span> VERIFYING REPO…`;

  try {
    const formData = new FormData();
    formData.append('github_url', url);
    formData.append('project_title', name || 'Project');
    formData.append('claimed_technologies', tech);

    const res = await fetch('/api/verify-project', {
      method: 'POST',
      body: formData
    });

    const result = await res.json();
    directResultsBox.classList.remove('hidden');
    directResultsJson.innerHTML = `
      <div class="space-y-3">
        <div class="flex justify-between border-b border-outline-variant/30 pb-2">
          <span class="text-outline">Target Repository:</span>
          <span class="text-primary font-bold">${result.github_repository?.full_name || url}</span>
        </div>
        <div class="flex justify-between border-b border-outline-variant/30 pb-2">
          <span class="text-outline">Overall Evidence Score:</span>
          <span class="text-tertiary font-bold">${result.verification?.overall_evidence_score || 0}%</span>
        </div>
        <div>
          <span class="text-outline block mb-2">Claim Verification Details:</span>
          <div class="space-y-1.5">
            ${(result.verification?.project_reports[0]?.claims_breakdown || []).map(c => `
              <div class="flex justify-between p-2 rounded bg-surface-container border border-outline-variant/30">
                <span>${c.claim}</span>
                <span class="${c.badge === 'verified' ? 'text-tertiary font-bold' : (c.badge === 'partial' ? 'text-amber-300 font-bold' : 'text-error')}">${c.status} (${Math.round(c.similarity_score)}%)</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
    showToast('check_circle', 'GitHub repository verified successfully!');
  } catch (err) {
    showToast('error', 'Failed to verify repository.');
  } finally {
    directVerifyBtn.disabled = false;
    directVerifyBtn.innerHTML = `<span class="material-symbols-outlined text-[16px]">search_check</span> RUN DIRECT VERIFICATION`;
  }
});

// Toast notification
let toastTimer = null;
function showToast(icon, msg, duration = 4500) {
  toastIcon.textContent = icon;
  toastMsg.textContent  = msg;
  toast.classList.remove('hidden');
  toast.classList.add('flex');

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.classList.add('hidden');
    toast.classList.remove('flex');
  }, duration);
}
