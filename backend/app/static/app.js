/**
 * RESUME_INTEL — Multi-Source Cyber-Intelligence System Frontend Engine
 * Controls: 3D Three.js Particle Network, Tabs, File Upload, API Analytics, GitHub Multi-Repo, and LinkedIn Intelligence
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

const fileExtractStatus   = document.getElementById('file-extract-status');
const extractStatusText   = document.getElementById('extract-status-text');
const extractSpinner      = document.getElementById('extract-spinner');
const extractFoundChips   = document.getElementById('extract-found-chips');

const linksToggle         = document.getElementById('links-toggle');
const toggleArrow         = document.getElementById('toggle-arrow');
const optionalLinksBody   = document.getElementById('optional-links-body');
const linksDetectedBadge  = document.getElementById('links-detected-badge');
const linksStatusBanner   = document.getElementById('links-status-banner');
const linksStatusText     = document.getElementById('links-status-text');

const githubOverride      = document.getElementById('github-override');
const githubDetectedTag   = document.getElementById('github-detected-tag');
const linkedinOverride    = document.getElementById('linkedin-override');
const linkedinDetectedTag = document.getElementById('linkedin-detected-tag');
const portfolioOverride   = document.getElementById('portfolio-override');
const portfolioDetectedTag= document.getElementById('portfolio-detected-tag');

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
const subGhVal          = document.getElementById('sub-gh-val');
const subGhBar          = document.getElementById('sub-gh-bar');
const subLiVal          = document.getElementById('sub-li-val');
const subLiBar          = document.getElementById('sub-li-bar');

// LinkedIn Card
const linkedinCard      = document.getElementById('linkedin-intel-card');
const liHeadline        = document.getElementById('li-headline');
const liAbout           = document.getElementById('li-about');
const liCertsList       = document.getElementById('li-certifications-list');
const liPostsList       = document.getElementById('li-posts-list');
const liStatusBadge     = document.getElementById('linkedin-status-badge');

// Evidence Section
const pillVerified      = document.getElementById('pill-verified');
const pillPartial       = document.getElementById('pill-partial');
const pillUnsupported   = document.getElementById('pill-unsupported');
const reposContainer    = document.getElementById('repos-preview-container');
const claimsTbody       = document.getElementById('claims-tbody');

// Inconsistency
const inconsistencyAlert   = document.getElementById('inconsistency-alert');
const inconsistencyMessage = document.getElementById('inconsistency-message');

// Identity & Fraud Risk Verification Elements
const identityFraudCard     = document.getElementById('identity-fraud-card');
const identityVerdictBadge  = document.getElementById('identity-verdict-badge');
const identityTargetProfile = document.getElementById('identity-target-profile');
const identityOwnershipScore= document.getElementById('identity-ownership-score');
const identityScoreCircle   = document.getElementById('identity-score-circle');
const identityCalloutBanner = document.getElementById('identity-callout-banner');
const identityBannerIcon    = document.getElementById('identity-banner-icon');
const identityBannerText    = document.getElementById('identity-banner-text');
const identitySignalsGrid   = document.getElementById('identity-signals-grid');
const identitySignalsCount  = document.getElementById('identity-signals-count');
const candidateIdentityPill = document.getElementById('candidate-identity-pill');
const candidateIdentityText = document.getElementById('candidate-identity-text');

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

// Layer D: Code Quality & Authenticity
const layerDCard        = document.getElementById('layer-d-card');
const layerDVerdictBadge= document.getElementById('layer-d-verdict-badge');
const layerDScoreCircle = document.getElementById('layer-d-score-circle');
const layerDScoreNum    = document.getElementById('layer-d-score-num');
const layerDTierLabel   = document.getElementById('layer-d-tier-label');
const layerDCommitMeta  = document.getElementById('layer-d-commit-meta');
const layerDHighlights  = document.getElementById('layer-d-highlights');
const layerDRepoAudits  = document.getElementById('layer-d-repo-audits');
const layerDDimGrid     = document.getElementById('layer-d-dimensions-grid');
const layerDPenaltyBanner = document.getElementById('layer-d-penalty-banner');
const layerDPenaltyText = document.getElementById('layer-d-penalty-text');
const layerDAnomalyText = document.getElementById('layer-d-anomaly-text');

// Contribution Graph
const contribGraphCard  = document.getElementById('contrib-graph-card');
const contribBarsContainer = document.getElementById('contrib-bars-container');
const contribTotalBadge = document.getElementById('contrib-total-badge');
const contribYearsBadge = document.getElementById('contrib-years-badge');
const contribYearPopup  = document.getElementById('contrib-year-popup');
const contribPopupYear  = document.getElementById('contrib-popup-year');
const contribPopupTotal = document.getElementById('contrib-popup-total');
const contribPopupRepos = document.getElementById('contrib-popup-repos');

// ── State ────────────────────────────────────────────────────────────────────
let selectedFile = null;
let currentReportData = null;
const CIRCUMFERENCE = 427; // 2 * PI * 68

// ── Tab Switching ────────────────────────────────────────────────────────────
function activateTab(targetId) {
  document.querySelectorAll('.view-content').forEach(v => v.classList.add('tab-hidden'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  const targetView = document.getElementById(targetId);
  if (targetView) targetView.classList.remove('tab-hidden');
  const matchingTab = document.querySelector(`.nav-tab[data-target="${targetId}"]`);
  if (matchingTab) matchingTab.classList.add('active');
}

document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => activateTab(tab.getAttribute('data-target')));
});

// Initialise first tab visible on page load
activateTab('tab-match-engine');

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
  fileSelectedView.classList.add('flex');

  // Trigger instant auto-extraction of candidate links & profiles
  autoFetchResumeLinks(file);
}

async function autoFetchResumeLinks(file) {
  if (!file) return;
  
  if (fileExtractStatus) {
    fileExtractStatus.classList.remove('hidden');
    fileExtractStatus.classList.add('flex');
    extractStatusText.innerHTML = `
      <span class="btn-spinner inline-block w-3 h-3 border-2"></span>
      <span>Auto-extracting LinkedIn, GitHub &amp; Portfolio…</span>
    `;
    if (extractFoundChips) {
      extractFoundChips.classList.add('hidden');
      extractFoundChips.innerHTML = '';
    }
  }

  try {
    const formData = new FormData();
    formData.append('resume_file', file);

    const res = await fetch('/api/parse-resume-preview', {
      method: 'POST',
      body: formData,
    });

    if (res.ok) {
      const data = await res.json();
      let detectedCount = 0;
      const chipHtml = [];

      // 1. GitHub
      if (data.github_url) {
        githubOverride.value = data.github_url;
        if (githubDetectedTag) githubDetectedTag.classList.remove('hidden');
        chipHtml.push(`<span class="px-1.5 py-0.5 rounded bg-primary/20 text-primary text-[9px] font-bold">GitHub</span>`);
        detectedCount++;
      } else {
        if (githubDetectedTag) githubDetectedTag.classList.add('hidden');
      }

      // 2. LinkedIn
      if (data.linkedin_url) {
        linkedinOverride.value = data.linkedin_url;
        if (linkedinDetectedTag) linkedinDetectedTag.classList.remove('hidden');
        chipHtml.push(`<span class="px-1.5 py-0.5 rounded bg-blue-400/20 text-blue-400 text-[9px] font-bold">LinkedIn</span>`);
        detectedCount++;
      } else {
        if (linkedinDetectedTag) linkedinDetectedTag.classList.add('hidden');
      }

      // 3. Portfolio
      if (data.portfolio_url) {
        portfolioOverride.value = data.portfolio_url;
        if (portfolioDetectedTag) portfolioDetectedTag.classList.remove('hidden');
        chipHtml.push(`<span class="px-1.5 py-0.5 rounded bg-pink-400/20 text-pink-400 text-[9px] font-bold">Portfolio</span>`);
        detectedCount++;
      } else {
        if (portfolioDetectedTag) portfolioDetectedTag.classList.add('hidden');
      }

      // Update status line
      if (fileExtractStatus) {
        if (detectedCount > 0) {
          extractStatusText.innerHTML = `
            <span class="material-symbols-outlined text-[13px] text-tertiary">check_circle</span>
            <span class="text-tertiary font-bold">${detectedCount} public link${detectedCount > 1 ? 's' : ''} auto-fetched</span>
          `;
          if (extractFoundChips) {
            extractFoundChips.innerHTML = chipHtml.join('');
            extractFoundChips.classList.remove('hidden');
          }

          // Open Links section & show auto-detect banners
          optionalLinksBody.classList.remove('hidden');
          toggleArrow.textContent = 'expand_less';
          if (linksDetectedBadge) linksDetectedBadge.classList.remove('hidden');
          if (linksStatusBanner) {
            linksStatusBanner.classList.remove('hidden');
            linksStatusBanner.classList.add('flex');
            linksStatusText.textContent = `Auto-fetched ${detectedCount} profile link${detectedCount > 1 ? 's' : ''} from resume. You may verify or edit them below.`;
          }

          showToast('verified', `Auto-fetched ${detectedCount} public profile link${detectedCount > 1 ? 's' : ''} from ${file.name}!`);
        } else {
          extractStatusText.innerHTML = `
            <span class="material-symbols-outlined text-[13px] text-on-surface-variant">info</span>
            <span class="text-on-surface-variant">No explicit profile links in text · Optional override available below</span>
          `;
        }
      }

      // If candidate name extracted, annotate file view
      if (data.candidate_name && data.candidate_name !== 'Candidate') {
        fileNameDisplay.textContent = `${file.name} (${data.candidate_name})`;
      }

    }
  } catch (err) {
    console.warn('Auto link preview error:', err);
    if (fileExtractStatus) {
      extractStatusText.innerHTML = `
        <span class="text-outline text-[10px]">Ready for analysis</span>
      `;
    }
  }
}

function clearFile() {
  selectedFile = null;
  resumeInput.value = '';
  dropZoneContent.classList.remove('hidden');
  fileSelectedView.classList.add('hidden');
  fileSelectedView.classList.remove('flex');
  
  if (fileExtractStatus) fileExtractStatus.classList.add('hidden');
  if (githubDetectedTag) githubDetectedTag.classList.add('hidden');
  if (linkedinDetectedTag) linkedinDetectedTag.classList.add('hidden');
  if (portfolioDetectedTag) portfolioDetectedTag.classList.add('hidden');
  if (linksDetectedBadge) linksDetectedBadge.classList.add('hidden');
  if (linksStatusBanner) linksStatusBanner.classList.add('hidden');
  
  githubOverride.value = '';
  linkedinOverride.value = '';
  portfolioOverride.value = '';
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
      githubOverride.value = data.sample_github_repo || 'https://github.com/swapnilsupe01';
      linkedinOverride.value = data.sample_linkedin_url || 'https://linkedin.com/in/swapnilsupe01';
      optionalLinksBody.classList.remove('hidden');
      toggleArrow.textContent = 'expand_less';
      showToast('play_arrow', 'Demo ML JD, GitHub user profile & LinkedIn loaded! Select your resume PDF to analyze.');
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
    if (linkedinOverride.value.trim()) {
      formData.append('linkedin_url', linkedinOverride.value.trim());
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
    btnLabel.textContent = 'ANALYZING & VERIFYING MULTI-SOURCE EVIDENCE…';
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
  const emailHtml = data.email !== 'Not Found' ? `<a href="mailto:${data.email}" class="hover:text-primary hover:underline">${data.email}</a>` : 'Email not listed';
  const phoneHtml = data.phone !== 'Not Found' ? `<span>${data.phone}</span>` : '';
  const ghHtml = (data.parsed_data?.github_urls || []).slice(0, 1).map(u => 
    `<a href="${u}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-0.5 text-primary font-semibold">GitHub <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`
  ).join(' • ');
  const liHtml = (data.parsed_data?.linkedin_urls || []).slice(0, 1).map(u => 
    `<a href="${u}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-0.5 text-blue-400 font-semibold">LinkedIn <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`
  ).join(' • ');

  const contactParts = [emailHtml, phoneHtml, ghHtml, liHtml].filter(Boolean);
  candidateContact.innerHTML = contactParts.join(' • ');

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
    animateBar(subGhVal,    subGhBar,    pe.github_score || 0);
    animateBar(subLiVal,    subLiBar,    pe.linkedin_score || 0);
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

  // Identity Verification & Fraud Risk Intelligence
  renderIdentityFraudReport(pe.identity_verification, data.candidate_name);

  // Layer D: Code Quality & Authenticity Forensics
  renderLayerD(data.code_quality);

  // Contribution Graph (from Layer D commit data)
  if (data.code_quality && data.code_quality.contribution_graph) {
    renderContributionGraph(data.code_quality.contribution_graph);
  }

  // LinkedIn Intelligence Rendering
  renderLinkedInIntel(pe.linkedin_profile);

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

function renderIdentityFraudReport(identityData, candidateNameStr) {
  if (!identityData || !identityData.verifications || identityData.verifications.length === 0) {
    if (identityFraudCard) identityFraudCard.classList.add('hidden');
    if (candidateIdentityPill) candidateIdentityPill.classList.add('hidden');
    return;
  }

  const primary = identityData.primary || identityData.verifications[0];
  if (!primary) return;

  if (identityFraudCard) identityFraudCard.classList.remove('hidden');

  const badge = primary.ownership_badge || 'uncertain';
  const score = Math.round(primary.ownership_score || 0);
  const username = primary.github_username || 'candidate';
  const verdict = primary.ownership_verdict || 'Evaluation Complete';
  const message = primary.ownership_message || '';

  // 1. Candidate Header Pill
  if (candidateIdentityPill && candidateIdentityText) {
    candidateIdentityPill.classList.remove('hidden', 'bg-tertiary/15', 'text-tertiary', 'border-tertiary/30',
      'bg-amber-500/15', 'text-amber-400', 'border-amber-500/30', 'bg-error/15', 'text-error', 'border-error/30');

    if (badge === 'confirmed') {
      candidateIdentityPill.classList.add('bg-tertiary/15', 'text-tertiary', 'border-tertiary/30');
      candidateIdentityText.textContent = `GitHub Verified: @${username}`;
    } else if (badge === 'likely') {
      candidateIdentityPill.classList.add('bg-amber-500/15', 'text-amber-400', 'border-amber-500/30');
      candidateIdentityText.textContent = `GitHub Likely: @${username}`;
    } else if (badge === 'uncertain') {
      candidateIdentityPill.classList.add('bg-amber-500/15', 'text-amber-400', 'border-amber-500/30');
      candidateIdentityText.textContent = `Ownership Unverified: @${username}`;
    } else {
      candidateIdentityPill.classList.add('bg-error/15', 'text-error', 'border-error/30');
      candidateIdentityText.textContent = `Identity Mismatch: @${username}`;
    }
  }

  // 2. Card Header Badges & Colors
  if (identityVerdictBadge) {
    identityVerdictBadge.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border ';
    if (badge === 'confirmed') {
      identityVerdictBadge.className += 'bg-tertiary/15 text-tertiary border-tertiary/30';
    } else if (badge === 'likely') {
      identityVerdictBadge.className += 'bg-amber-500/15 text-amber-400 border-amber-500/30';
    } else if (badge === 'uncertain') {
      identityVerdictBadge.className += 'bg-orange-500/15 text-orange-400 border-orange-500/30';
    } else {
      identityVerdictBadge.className += 'bg-error/15 text-error border-error/30';
    }
    identityVerdictBadge.textContent = verdict.toUpperCase();
  }

  if (identityTargetProfile) {
    identityTargetProfile.innerHTML = `Audited target account: <a href="https://github.com/${username}" target="_blank" rel="noopener noreferrer" class="text-cyan font-bold hover:underline">github.com/${username}</a> for candidate <strong class="text-white">${candidateNameStr || primary.candidate_name}</strong>`;
  }

  if (identityOwnershipScore) {
    identityOwnershipScore.textContent = `${score}%`;
    if (badge === 'confirmed') {
      identityOwnershipScore.className = 'font-headline-lg text-xl font-extrabold text-tertiary';
    } else if (badge === 'likely') {
      identityOwnershipScore.className = 'font-headline-lg text-xl font-extrabold text-yellow-400';
    } else if (badge === 'uncertain') {
      identityOwnershipScore.className = 'font-headline-lg text-xl font-extrabold text-orange-400';
    } else {
      identityOwnershipScore.className = 'font-headline-lg text-xl font-extrabold text-error';
    }
  }

  if (identityScoreCircle) {
    identityScoreCircle.setAttribute('stroke-dasharray', `${score}, 100`);
    if (badge === 'confirmed') {
      identityScoreCircle.setAttribute('class', 'text-tertiary transition-all duration-1000');
    } else if (badge === 'likely') {
      identityScoreCircle.setAttribute('class', 'text-yellow-400 transition-all duration-1000');
    } else if (badge === 'uncertain') {
      identityScoreCircle.setAttribute('class', 'text-orange-400 transition-all duration-1000');
    } else {
      identityScoreCircle.setAttribute('class', 'text-error transition-all duration-1000');
    }
  }

  // 3. Callout Banner
  if (identityCalloutBanner) {
    identityCalloutBanner.className = 'p-3.5 rounded-xl text-xs leading-relaxed mb-5 border font-body-md flex items-start gap-3 ';
    if (badge === 'confirmed') {
      identityCalloutBanner.className += 'bg-tertiary/10 border-tertiary/25 text-tertiary';
      if (identityBannerIcon) identityBannerIcon.textContent = 'verified_user';
    } else if (badge === 'likely') {
      identityCalloutBanner.className += 'bg-yellow-500/10 border-yellow-500/25 text-yellow-200';
      if (identityBannerIcon) identityBannerIcon.textContent = 'gpp_maybe';
    } else if (badge === 'uncertain') {
      identityCalloutBanner.className += 'bg-orange-500/10 border-orange-500/25 text-orange-200';
      if (identityBannerIcon) identityBannerIcon.textContent = 'warning';
    } else {
      identityCalloutBanner.className += 'bg-error/15 border-error/40 text-error';
      if (identityBannerIcon) identityBannerIcon.textContent = 'report';
    }

    let penaltyNoteHtml = '';
    if (identityData.ownership_penalty_applied && identityData.ownership_penalty_note) {
      penaltyNoteHtml = `<div class="mt-2 pt-2 border-t border-current/20 font-code-sm text-[11px] font-bold">⚠️ ${identityData.ownership_penalty_note}</div>`;
    }

    if (identityBannerText) {
      identityBannerText.innerHTML = `<strong>${verdict}:</strong> ${message}${penaltyNoteHtml}`;
    }
  }

  // 4. Render 10 Signals Breakdown Grid
  if (identitySignalsGrid && primary.signals) {
    identitySignalsGrid.innerHTML = '';
    const signalKeys = Object.keys(primary.signals);
    if (identitySignalsCount) {
      identitySignalsCount.textContent = `${signalKeys.length} Signals Monitored`;
    }

    signalKeys.forEach(k => {
      const sig = primary.signals[k];
      const sigCard = document.createElement('div');
      sigCard.className = 'bg-surface-container-lowest/70 border border-outline-variant/30 rounded-xl p-3 flex flex-col justify-between hover:border-outline-variant/60 transition-all';

      let statusBadge = '';
      let statusIcon = 'check_circle';
      let statusColor = 'text-tertiary';

      if (!sig.available) {
        statusBadge = '<span class="text-[10px] text-outline bg-surface-container px-2 py-0.5 rounded border border-outline-variant/30 font-code-sm">Unavailable</span>';
        statusIcon = 'remove_circle_outline';
        statusColor = 'text-outline';
      } else if (sig.score >= 80) {
        statusBadge = `<span class="text-[10px] text-tertiary bg-tertiary/10 px-2 py-0.5 rounded border border-tertiary/30 font-code-sm font-bold">${Math.round(sig.score)}% Pass</span>`;
        statusIcon = 'verified';
        statusColor = 'text-tertiary';
      } else if (sig.score >= 40) {
        statusBadge = `<span class="text-[10px] text-yellow-400 bg-yellow-500/10 px-2 py-0.5 rounded border border-yellow-500/30 font-code-sm font-bold">${Math.round(sig.score)}% Partial</span>`;
        statusIcon = 'warning';
        statusColor = 'text-yellow-400';
      } else {
        statusBadge = `<span class="text-[10px] text-error bg-error/10 px-2 py-0.5 rounded border border-error/30 font-code-sm font-bold">${Math.round(sig.score)}% Fail</span>`;
        statusIcon = 'cancel';
        statusColor = 'text-error';
      }

      sigCard.innerHTML = `
        <div class="flex items-center justify-between gap-2 mb-1.5">
          <span class="font-bold text-white flex items-center gap-1.5 truncate">
            <span class="material-symbols-outlined text-[15px] ${statusColor}">${statusIcon}</span>
            <span class="truncate">${sig.label}</span>
          </span>
          <div class="flex items-center gap-1.5 flex-shrink-0">
            <span class="text-[10px] text-outline font-code-sm">Weight: ${sig.weight}</span>
            ${statusBadge}
          </div>
        </div>
        <p class="text-[11px] text-on-surface-variant leading-relaxed">
          ${sig.explanation || 'Signal evaluated successfully.'}
        </p>
      `;

      identitySignalsGrid.appendChild(sigCard);
    });
  }
}

// ── Layer D: Code Quality & Authenticity Forensics ──────────────────────────
function renderLayerD(cq) {
  if (!cq || !cq.is_available) {
    if (layerDCard) layerDCard.classList.add('hidden');
    return;
  }
  layerDCard.classList.remove('hidden');

  const score = Math.round(cq.overall_authenticity_score || 0);
  const tier = cq.overall_quality_tier || 'basic';
  const tierLabel = cq.overall_quality_tier_label || 'Evaluating';

  // Verdict badge color
  const tierColors = {
    production: 'bg-tertiary/15 text-tertiary border-tertiary/30',
    competent:  'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
    basic:      'bg-orange-500/15 text-orange-400 border-orange-500/30',
    tutorial:   'bg-error/15 text-error border-error/30',
  };
  const tierIcons = { production: '🟢', competent: '🟡', basic: '🟠', tutorial: '🔴' };

  if (layerDVerdictBadge) {
    layerDVerdictBadge.className = `font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border ${tierColors[tier] || ''}`;
    layerDVerdictBadge.textContent = `${tierIcons[tier] || ''} ${tierLabel.toUpperCase()}`;
  }

  // Radial score
  if (layerDScoreCircle) layerDScoreCircle.setAttribute('stroke-dasharray', `${score}, 100`);
  if (layerDScoreNum) layerDScoreNum.textContent = `${score}%`;
  if (layerDTierLabel) layerDTierLabel.textContent = tierLabel;

  // Commit meta from first repo audit
  const firstAudit = (cq.repo_audits || [])[0];
  if (firstAudit && layerDCommitMeta) {
    layerDCommitMeta.textContent = `${firstAudit.total_commits} commits · ${firstAudit.commit_span_days} days span`;
  }

  // Anomaly badge
  if (layerDAnomalyText && firstAudit) {
    layerDAnomalyText.textContent = `Isolation Forest: ${firstAudit.anomaly_label || '—'}`;
  }

  // Aggregate highlights from all repos
  if (layerDHighlights) {
    layerDHighlights.innerHTML = '';
    const allHighlights = (cq.repo_audits || []).flatMap(r => r.highlights || []).slice(0, 6);
    allHighlights.forEach(h => {
      const iconMap = { pass: 'check_circle', fail: 'cancel', warn: 'warning' };
      const colorMap = { pass: 'text-tertiary', fail: 'text-error', warn: 'text-amber-400' };
      const icon = iconMap[h.status] || 'info';
      const color = colorMap[h.status] || 'text-outline';
      layerDHighlights.innerHTML += `
        <div class="flex items-center gap-2 text-xs py-1.5 px-3 rounded-lg bg-surface-container-lowest/60 border border-outline-variant/25">
          <span class="material-symbols-outlined text-[15px] ${color}">${icon}</span>
          <span class="text-on-surface-variant">${h.text}</span>
        </div>`;
    });
  }

  // Per-Repo Audit Cards
  if (layerDRepoAudits) {
    layerDRepoAudits.innerHTML = '';
    (cq.repo_audits || []).forEach(r => {
      const rScore = Math.round(r.authenticity_score || 0);
      const rTier = r.quality_tier || 'basic';
      const rColor = tierColors[rTier] || '';
      const repoUrl = `https://github.com/${r.repo_full_name}`;
      const intentHtml = Object.entries(r.commit_intent_distribution || {})
        .map(([k, v]) => `<span class="px-1.5 py-0.5 rounded bg-surface-container border border-outline-variant/30 font-code-sm text-[10px] text-on-surface-variant">${k}: ${v}</span>`)
        .join(' ');

      layerDRepoAudits.innerHTML += `
        <div class="p-4 rounded-xl bg-surface-container-lowest/70 border border-purple-500/20 hover:border-purple-500/50 transition-all">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-purple-400 text-[16px]">folder_code</span>
              <a href="${repoUrl}" target="_blank" rel="noopener noreferrer" class="font-bold text-xs text-white hover:text-purple-300 hover:underline flex items-center gap-1">
                ${r.repo_full_name}
                <span class="material-symbols-outlined text-[12px]">open_in_new</span>
              </a>
            </div>
            <div class="flex items-center gap-2 flex-shrink-0">
              <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full border ${rColor} font-bold">${tierIcons[rTier]} ${Math.round(rScore)}%</span>
              <span class="font-code-sm text-[10px] text-outline">${r.total_commits} commits · ${r.commit_span_days}d</span>
            </div>
          </div>
          ${intentHtml ? `<div class="flex flex-wrap gap-1.5 mb-2"><span class="text-[10px] text-outline font-code-sm mr-1">Commit Intents:</span>${intentHtml}</div>` : ''}
          <div class="text-[10px] font-code-sm text-outline">Anomaly Score: ${r.anomaly_score} — ${r.anomaly_label}</div>
        </div>`;
    });
  }

  // 5-Dimension Breakdown Grid
  if (layerDDimGrid) {
    layerDDimGrid.innerHTML = '';
    const firstRepoAudit = (cq.repo_audits || [])[0];
    const dims = firstRepoAudit ? firstRepoAudit.dimensions : null;
    if (dims) {
      Object.entries(dims).forEach(([key, d]) => {
        const s = Math.round(d.score || 0);
        let statusColor = s >= 75 ? 'text-tertiary' : s >= 40 ? 'text-yellow-400' : 'text-error';
        let statusIcon  = s >= 75 ? 'verified' : s >= 40 ? 'warning' : 'cancel';
        let badgeColor  = s >= 75 ? 'bg-tertiary/10 text-tertiary border-tertiary/30'
                        : s >= 40 ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
                        : 'bg-error/10 text-error border-error/30';
        layerDDimGrid.innerHTML += `
          <div class="bg-surface-container-lowest/70 border border-purple-500/15 rounded-xl p-3 hover:border-purple-500/40 transition-all">
            <div class="flex items-center justify-between gap-2 mb-1.5">
              <span class="font-bold text-white text-xs flex items-center gap-1.5 truncate">
                <span class="material-symbols-outlined text-[14px] ${statusColor}">${statusIcon}</span>
                <span class="truncate">${d.label}</span>
              </span>
              <div class="flex items-center gap-1.5 flex-shrink-0">
                <span class="text-[10px] text-outline font-code-sm">${d.weight}</span>
                <span class="text-[10px] px-1.5 py-0.5 rounded border font-code-sm font-bold ${badgeColor}">${s}%</span>
              </div>
            </div>
            <p class="text-[11px] text-on-surface-variant leading-relaxed">${d.explanation || ''}</p>
          </div>`;
      });
    }
  }

  // Penalty banner
  if (cq.layer_d_penalty_applied && layerDPenaltyBanner) {
    layerDPenaltyBanner.classList.remove('hidden');
    if (layerDPenaltyText) layerDPenaltyText.textContent = cq.layer_d_penalty_note || '';
  } else if (layerDPenaltyBanner) {
    layerDPenaltyBanner.classList.add('hidden');
  }
}

// ── GitHub Contribution Graph ─────────────────────────────────────────────────
function renderContributionGraph(graphData) {
  if (!graphData || !graphData.years_active || graphData.years_active.length === 0) {
    if (contribGraphCard) contribGraphCard.classList.add('hidden');
    return;
  }

  contribGraphCard.classList.remove('hidden');

  const years = graphData.years_active;
  const totals = graphData.yearly_totals;
  const perRepo = graphData.per_repo_by_year;
  const totalCommits = graphData.total_tracked_commits || 0;
  const maxCommits = Math.max(...Object.values(totals), 1);

  // Update badges
  if (contribTotalBadge) contribTotalBadge.textContent = `${totalCommits} Total Commits`;
  if (contribYearsBadge) contribYearsBadge.textContent = `${years.length} Year${years.length !== 1 ? 's' : ''} Active`;

  // Build bar chart
  contribBarsContainer.innerHTML = '';
  let activeYear = null;

  years.forEach(year => {
    const count = totals[year] || 0;
    const heightPct = Math.max(8, Math.round((count / maxCommits) * 100));
    const intensity = count / maxCommits;
    const opacity = intensity > 0.7 ? '70' : intensity > 0.4 ? '45' : '20';

    const barWrapper = document.createElement('div');
    barWrapper.className = 'flex flex-col items-center gap-1 cursor-pointer group flex-1 min-w-0';
    barWrapper.setAttribute('data-year', year);
    barWrapper.setAttribute('data-count', count);
    barWrapper.title = `${year}: ${count} commits — click for breakdown`;

    barWrapper.innerHTML = `
      <span class="text-[10px] font-code-sm text-primary font-bold opacity-0 group-hover:opacity-100 transition-opacity">${count}</span>
      <div class="w-full rounded-t-md transition-all duration-500 group-hover:scale-105 group-hover:shadow-lg group-hover:shadow-primary/20 bg-primary/${opacity}"
           style="height: ${heightPct}%; min-height: 8px;">
      </div>
      <span class="text-[10px] font-code-sm text-outline group-hover:text-primary transition-colors">${year}</span>`;

    barWrapper.addEventListener('click', () => {
      // Deactivate all bars
      contribBarsContainer.querySelectorAll('[data-year]').forEach(b => {
        b.querySelector('div').classList.remove('ring-2', 'ring-primary', 'ring-offset-1', 'ring-offset-transparent');
      });

      if (activeYear === year) {
        // Toggle off
        activeYear = null;
        if (contribYearPopup) contribYearPopup.classList.add('hidden');
        return;
      }

      activeYear = year;
      barWrapper.querySelector('div').classList.add('ring-2', 'ring-primary');

      // Build popup
      if (contribYearPopup) {
        contribYearPopup.classList.remove('hidden');
        if (contribPopupYear) contribPopupYear.textContent = `${year} — ${count} commits`;
        if (contribPopupTotal) contribPopupTotal.textContent = `${count} total commits across all repos`;

        const reposThisYear = (perRepo[year] || []).sort((a, b) => b.commits - a.commits);
        if (contribPopupRepos) {
          if (reposThisYear.length === 0) {
            contribPopupRepos.innerHTML = '<p class="text-outline">No per-repo breakdown available.</p>';
          } else {
            contribPopupRepos.innerHTML = reposThisYear.map(r => {
              const pct = Math.round((r.commits / count) * 100);
              const tierColor = { production: 'text-tertiary', competent: 'text-yellow-400', basic: 'text-orange-400', tutorial: 'text-error' }[r.quality_tier] || 'text-outline';
              return `
                <div class="flex items-center gap-3">
                  <div class="flex-1">
                    <div class="flex items-center justify-between mb-1">
                      <span class="font-bold text-white text-xs">${r.repo}</span>
                      <span class="font-code-sm text-[10px] text-primary font-bold">${r.commits} commits</span>
                    </div>
                    <div class="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                      <div class="h-full bg-primary rounded-full transition-all duration-700" style="width:${pct}%"></div>
                    </div>
                  </div>
                  <span class="font-code-sm text-[10px] ${tierColor} flex-shrink-0">${r.authenticity_score}%</span>
                </div>`;
            }).join('');
          }
        }
        // Scroll popup into view
        contribYearPopup.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });

    contribBarsContainer.appendChild(barWrapper);
  });
}

function renderLinkedInIntel(li) {
  if (!li || !li.is_accessible) {
    linkedinCard.classList.add('hidden');
    return;
  }
  linkedinCard.classList.remove('hidden');
  const liUrl = li.url || `https://linkedin.com/in/${li.username || 'swapnilsupe01'}`;
  liHeadline.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-1">${li.headline || 'Professional Profile'} <span class="material-symbols-outlined text-[13px] text-blue-400">open_in_new</span></a>`;
  liAbout.textContent = li.about || 'Public LinkedIn profile verified.';
  liStatusBadge.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:underline flex items-center gap-1">Profile Verified <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`;

  liCertsList.innerHTML = '';
  const certs = li.certifications || [];
  if (certs.length > 0) {
    certs.forEach(c => {
      const liEl = document.createElement('li');
      liEl.className = 'flex items-center gap-1.5';
      liEl.innerHTML = `<span class="material-symbols-outlined text-[14px]">verified</span><span>${c}</span>`;
      liCertsList.appendChild(liEl);
    });
  } else {
    liCertsList.innerHTML = `<li class="text-outline">No specific licenses listed.</li>`;
  }

  liPostsList.innerHTML = '';
  const posts = li.recent_post_topics || [];
  if (posts.length > 0) {
    posts.forEach(p => {
      const liEl = document.createElement('li');
      liEl.className = 'flex items-start gap-1.5';
      liEl.innerHTML = `<span class="material-symbols-outlined text-[14px] text-blue-400 mt-0.5">forum</span><span>${p}</span>`;
      liPostsList.appendChild(liEl);
    });
  } else {
    liPostsList.innerHTML = `<li class="text-outline">General professional activity.</li>`;
  }
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
    card.className = 'p-4 rounded-lg bg-surface-container-lowest/70 border border-outline-variant/40 hover:border-primary transition-all flex flex-col justify-between group';
    const techTags = (r.technologies || []).slice(0, 5).map(t => 
      `<span class="px-2 py-0.5 rounded text-[11px] font-code-sm bg-surface-container text-on-surface-variant border border-outline-variant/30">${t}</span>`
    ).join(' ');

    const fullName = r.full_name || (r.owner ? `${r.owner}/${r.repo_name}` : r.repo_name);
    const repoUrl = r.url || `https://github.com/${fullName}`;

    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between gap-2 text-xs font-bold text-primary mb-1">
          <a href="${repoUrl}" target="_blank" rel="noopener noreferrer" class="flex items-center gap-1.5 truncate hover:underline hover:text-tertiary transition-colors" title="Open repository on GitHub">
            <span class="material-symbols-outlined text-[16px]">folder_code</span>
            <span class="truncate">${fullName}</span>
            <span class="material-symbols-outlined text-[13px] opacity-70 group-hover:opacity-100">open_in_new</span>
          </a>
          <span class="text-[10px] font-code-sm px-1.5 py-0.5 rounded bg-primary-container/20 text-primary flex-shrink-0">Public</span>
        </div>
        <p class="text-xs text-on-surface-variant line-clamp-2 mb-3">${r.description || 'Public GitHub repository'}</p>
        <div class="flex flex-wrap gap-1.5 mb-3">${techTags}</div>
      </div>
      <div class="pt-2 border-t border-outline-variant/20 flex justify-between items-center text-[11px] font-code-sm">
        <span class="text-outline">${(r.languages || []).join(', ') || 'Source Code'}</span>
        <a href="${repoUrl}" target="_blank" rel="noopener noreferrer" class="text-primary hover:text-tertiary flex items-center gap-1 font-semibold hover:underline">
          View on GitHub <span class="material-symbols-outlined text-[13px]">arrow_outward</span>
        </a>
      </div>
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

  claimsTbody.innerHTML = allClaims.map(c => {
    // Generate clickable link for snippet citation if URL available
    let citationHtml = `<div class="line-clamp-2" title="${c.evidence_snippet}">${c.evidence_snippet}</div>`;
    if (c.source_url) {
      citationHtml = `
        <div class="flex flex-col gap-1">
          <div class="line-clamp-2 text-on-surface" title="${c.evidence_snippet}">${c.evidence_snippet}</div>
          <a href="${c.source_url}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-[10px] font-code-sm text-primary hover:text-tertiary hover:underline w-fit">
            <span>Inspect Evidence Source</span>
            <span class="material-symbols-outlined text-[12px]">open_in_new</span>
          </a>
        </div>
      `;
    }

    return `
      <tr class="hover:bg-surface-container/30 transition-colors">
        <td class="p-3">
          <span class="font-semibold text-on-surface">${c.claim}</span>
          <div class="text-[10px] font-code-sm text-outline mt-0.5">Project: ${c.project_title}</div>
        </td>
        <td class="p-3"><span class="px-2 py-0.5 rounded font-code-sm text-[11px] bg-surface-container border border-outline-variant/30 text-on-surface-variant">${c.claim_type}</span></td>
        <td class="p-3 font-code-sm text-[11px] text-on-surface-variant max-w-sm">
          ${citationHtml}
        </td>
        <td class="p-3 font-code-sm font-bold text-primary">${Math.round(c.similarity_score)}%</td>
        <td class="p-3">
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-code-sm font-bold ${
            c.badge === 'verified' ? 'status-pill-verified' : (c.badge === 'partial' ? 'status-pill-partial' : 'status-pill-unsupported')
          }">
            ${c.badge === 'verified' ? '🟢 Verified' : (c.badge === 'partial' ? '🟡 Partial' : '🔴 Not Supported')}
          </span>
        </td>
      </tr>
    `;
  }).join('');
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

// ── Interactive Layer Detail Modal Controller ───────────────────────────────
(function initLayerDetailModal() {
  const modal          = document.getElementById('layer-detail-modal');
  const modalCard      = document.getElementById('layer-modal-card');
  const modalCloseBtn  = document.getElementById('layer-modal-close-btn');
  const modalConfirmBtn= document.getElementById('layer-modal-confirm-btn');
  const modalBadge     = document.getElementById('layer-modal-badge');
  const modalSubtitle  = document.getElementById('layer-modal-subtitle');
  const modalTitle     = document.getElementById('layer-modal-title');
  const modalIcon      = document.getElementById('layer-modal-icon');
  const modalIconWrap  = document.getElementById('layer-modal-icon-wrap');
  const modalTopBar    = document.getElementById('layer-modal-top-bar');
  const modalBody      = document.getElementById('layer-modal-body');

  if (!modal || !modalCard) return;

  const LAYER_DATA = {
    'layer-a': {
      badge: 'LAYER A · SEMANTIC MATCHING',
      badgeClass: 'bg-cyan/10 text-cyan border-cyan/30',
      subtitle: 'Natural Language Processing & Skill Alignment',
      title: 'Job Matching Engine',
      icon: 'join_inner',
      iconWrapClass: 'bg-cyan/10 border-cyan/30 text-cyan',
      topBarClass: 'bg-gradient-to-r from-primary via-cyan to-primary',
      html: `
        <div class="space-y-4 font-body-md text-xs">
          <p class="text-on-surface leading-relaxed">
            <strong>Layer A</strong> solves the core limitation of legacy ATS keyword scanners by evaluating candidates through dense semantic vector representations rather than naive token matches.
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-cyan font-bold font-code-sm block text-[11px] mb-1">Sentence-BERT (all-MiniLM-L6-v2)</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Transforms resume bullet points and job requirements into 384-dimensional embeddings. Computes pairwise cosine distance to recognize synonyms like <em>"REST API Development"</em> ↔ <em>"FastAPI Microservices"</em>.
              </p>
            </div>
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-cyan font-bold font-code-sm block text-[11px] mb-1">Multi-Model Gram Analysis</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Extracts TF-IDF term frequencies and Unigram, Bigram, and Trigram n-gram overlaps to assess both conceptual depth and phrase precision.
              </p>
            </div>
          </div>

          <div class="bg-surface-container-lowest/80 border border-outline-variant/30 rounded-xl p-3.5">
            <span class="text-outline font-code-sm text-[10px] block uppercase tracking-wider mb-2 font-bold">Key Subsystem Capabilities:</span>
            <ul class="space-y-1.5 text-[11px] text-on-surface-variant font-code-sm">
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-cyan text-[14px]">check_circle</span>
                <span>Structured extraction of required vs. preferred technical skills</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-cyan text-[14px]">check_circle</span>
                <span>Experience duration parsing &amp; education level threshold validation</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-cyan text-[14px]">check_circle</span>
                <span>Section completeness scoring (Certifications, Summary, Work History)</span>
              </li>
            </ul>
          </div>
        </div>
      `
    },

    'layer-b': {
      badge: 'LAYER B · PUBLIC EVIDENCE',
      badgeClass: 'bg-tertiary/10 text-tertiary border-tertiary/30',
      subtitle: 'Multi-Source Public Repository & Profile Verification',
      title: 'Project Evidence Engine',
      icon: 'fact_check',
      iconWrapClass: 'bg-tertiary/10 border-tertiary/30 text-tertiary',
      topBarClass: 'bg-gradient-to-r from-cyan via-tertiary to-emerald-400',
      html: `
        <div class="space-y-4 font-body-md text-xs">
          <p class="text-on-surface leading-relaxed">
            <strong>Layer B</strong> anchors candidate claims against empirical public evidence. Instead of trusting unsubstantiated claims on a PDF, the system crawls and cross-validates technical work on GitHub and LinkedIn.
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-tertiary font-bold font-code-sm block text-[11px] mb-1">Multi-Repo Deep Scanning</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Connects via GitHub REST APIs to analyze languages, README files, topic tags, and dependency manifests (<code>requirements.txt</code>, <code>package.json</code>) across all candidate repos.
              </p>
            </div>
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-tertiary font-bold font-code-sm block text-[11px] mb-1">3-State Claim Categorization</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Deconstructs projects into claims, assigning 🟢 <strong>Verified</strong> (≥80%), 🟡 <strong>Partially Supported</strong> (60–79%), or 🔴 <strong>Not Supported</strong> with direct citation snippets.
              </p>
            </div>
          </div>

          <div class="bg-surface-container-lowest/80 border border-outline-variant/30 rounded-xl p-3.5">
            <span class="text-outline font-code-sm text-[10px] block uppercase tracking-wider mb-2 font-bold">Key Subsystem Capabilities:</span>
            <ul class="space-y-1.5 text-[11px] text-on-surface-variant font-code-sm">
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-tertiary text-[14px]">check_circle</span>
                <span>Automatic URL extraction for GitHub, LinkedIn &amp; Portfolios</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-tertiary text-[14px]">check_circle</span>
                <span>Public LinkedIn career verification (headline, roles, certifications)</span>
              </li>
              <li class="flex items-center gap-2">
                <span class="material-symbols-outlined text-tertiary text-[14px]">check_circle</span>
                <span>Discrepancy warnings if code dependencies differ from resume claims</span>
              </li>
            </ul>
          </div>
        </div>
      `
    },

    'layer-c': {
      badge: 'LAYER C · NOVEL IDENTITY DEFENSE',
      badgeClass: 'bg-neon-purple/10 text-neon-purple border-neon-purple/30',
      subtitle: 'Recruiter-Side 10-Signal Anti-Spoofing Architecture',
      title: 'Identity & Fraud Defense',
      icon: 'fingerprint',
      iconWrapClass: 'bg-neon-purple/10 border-neon-purple/30 text-neon-purple',
      topBarClass: 'bg-gradient-to-r from-neon-purple via-pink-500 to-cyan',
      html: `
        <div class="space-y-4 font-body-md text-xs">
          <p class="text-on-surface leading-relaxed">
            <strong>Layer C</strong> is a novel anti-fraud defense built specifically for recruiters. It prevents candidates from pasting another developer's high-star GitHub URL into their resume to falsely claim their code.
          </p>

          <div class="bg-neon-purple/10 border border-neon-purple/25 rounded-xl p-3.5 text-[11px] text-neon-purple font-code-sm leading-relaxed">
            🛡️ <strong>The Identity Problem Solved:</strong> Candidate <em>"Swapnil Supe"</em> cannot paste <em>"github.com/swapnil-23"</em> (a random person with the same first name) or a famous repo. The system automatically detects the spoof and penalizes the evidence score by up to 80%.
          </div>

          <div class="bg-surface-container-lowest/80 border border-outline-variant/30 rounded-xl p-3.5">
            <span class="text-outline font-code-sm text-[10px] block uppercase tracking-wider mb-2 font-bold">10 Automated Recruiter-Side Signals:</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-code-sm">
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">1. Bio Display Name (18%)</span>: Matches GitHub profile name to resume.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">2. Username Tokens (8%)</span>: Split &amp; substring name token analysis.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">3. LinkedIn in Bio (18%)</span>: Verifies if GitHub bio links to candidate LinkedIn.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">4. Git Commit Authors (14%)</span>: Audits local git commit signatures.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">5. Public Email Match (2%)</span>: Cross-matches public email with resume.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">6. Account Age vs XP (10%)</span>: Flags 1-week-old accounts claiming 5yr XP.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">7. Commit Email Match (10%)</span>: Scans raw git commit header emails.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">8. Contribution History (5%)</span>: Repos, followers &amp; multi-year longevity.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">9. Profile README (5%)</span>: Scans <code># Hi, I'm...</code> intro markdown.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-neon-purple/30 bg-neon-purple/5">
                <span class="text-tertiary font-bold">10. LinkedIn Post → GitHub (10%)</span>: <strong>Crown Jewel</strong> — verifies if candidate publicly announced repo on LinkedIn!
              </div>
            </div>
          </div>
        </div>
      `
    },

    'layer-d': {
      badge: 'LAYER D · CODE FORENSICS',
      badgeClass: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
      subtitle: 'Codebase Quality, Originality & Anti-Template Engine',
      title: 'Code Quality & Authenticity Forensics',
      icon: 'manage_search',
      iconWrapClass: 'bg-purple-500/10 border-purple-500/30 text-purple-400',
      topBarClass: 'bg-gradient-to-r from-purple-500 via-fuchsia-400 to-pink-500',
      html: `
        <div class="space-y-4 font-body-md text-xs">
          <p class="text-on-surface leading-relaxed">
            <strong>Layer D</strong> answers the critical recruiter question: <em>"Did this candidate actually engineer this software, or did they fork someone else's repo, copy a YouTube tutorial, or dump a ZIP file in one commit?"</em>
          </p>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-purple-400 font-bold font-code-sm block text-[11px] mb-1">Isolation Forest Anomaly Model</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Applies unsupervised temporal modeling to commit intervals. Flags single-day ZIP dumps vs organic multi-week development cadences.
              </p>
            </div>
            <div class="bg-surface-container/70 border border-outline-variant/30 rounded-xl p-3.5">
              <span class="text-purple-400 font-bold font-code-sm block text-[11px] mb-1">Commit Message Intent NER</span>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                Uses NLP token classification to parse git commits into semantic intents (<code>feat</code>, <code>fix</code>, <code>refactor</code>, <code>docs</code>, <code>test</code>) vs lazy placeholders (<code>update</code>, <code>done</code>).
              </p>
            </div>
          </div>

          <div class="bg-surface-container-lowest/80 border border-outline-variant/30 rounded-xl p-3.5">
            <span class="text-outline font-code-sm text-[10px] block uppercase tracking-wider mb-2 font-bold">5 Forensic Inspection Dimensions:</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-code-sm">
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-purple-400 font-bold">1. Fork &amp; Upstream Origin (25%)</span>: Flags forked or derivative clones disguised as original creations.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-purple-400 font-bold">2. Commit Cadence (25%)</span>: Evaluates timeline span (days/weeks) to catch 1-commit ZIP-dumps.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-purple-400 font-bold">3. Commit Message Semantics (15%)</span>: Conventional semantic commit tags vs lazy messages.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-purple-400 font-bold">4. Tutorial Fingerprint (20%)</span>: Regex-scans for YouTube, Coursera, FreeCodeCamp starter kits.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20 sm:col-span-2">
                <span class="text-purple-400 font-bold">5. Production Standards (15%)</span>: Tests (<code>pytest/jest</code>), Docker (<code>Dockerfile</code>), and CI/CD (<code>.github/workflows</code>).
              </div>
            </div>
          </div>
        </div>
      `
    }
  };

  function openLayerModal(layerKey) {
    const data = LAYER_DATA[layerKey];
    if (!data) return;

    modalBadge.textContent    = data.badge;
    modalBadge.className      = `font-code-sm text-[10px] px-2.5 py-0.5 rounded font-bold border ${data.badgeClass}`;
    modalSubtitle.textContent = data.subtitle;
    modalTitle.textContent    = data.title;
    modalIcon.textContent     = data.icon;
    modalIconWrap.className   = `w-10 h-10 rounded-xl flex items-center justify-center border ${data.iconWrapClass}`;
    modalTopBar.className     = `h-1 ${data.topBarClass}`;
    modalBody.innerHTML       = data.html;

    modal.classList.remove('hidden');
    requestAnimationFrame(() => {
      modal.classList.remove('opacity-0');
      modalCard.classList.remove('scale-95');
      modalCard.classList.add('scale-100');
    });
  }

  function closeLayerModal() {
    modal.classList.add('opacity-0');
    modalCard.classList.remove('scale-100');
    modalCard.classList.add('scale-95');
    setTimeout(() => {
      modal.classList.add('hidden');
    }, 200);
  }

  // Bind click listeners on all layer cards in Project Flow
  document.querySelectorAll('.layer-modal-card').forEach(card => {
    card.addEventListener('click', () => {
      const layer = card.getAttribute('data-layer');
      if (layer) openLayerModal(layer);
    });

    card.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        const layer = card.getAttribute('data-layer');
        if (layer) openLayerModal(layer);
      }
    });
  });

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeLayerModal);
  if (modalConfirmBtn) modalConfirmBtn.addEventListener('click', closeLayerModal);

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeLayerModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
      closeLayerModal();
    }
  });
})();

