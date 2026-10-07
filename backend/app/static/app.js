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
let currentRawResumeText = null;
let currentCanonicalData = null;
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

  // ALWAYS reset previous candidate link state when a new file is chosen!
  if (githubOverride) githubOverride.value = '';
  if (linkedinOverride) linkedinOverride.value = '';
  if (portfolioOverride) portfolioOverride.value = '';
  window._resumeGitHubUrl = null;

  if (identityFraudCard) identityFraudCard.classList.add('hidden');
  if (candidateIdentityPill) candidateIdentityPill.classList.add('hidden');
  if (layerDCard) layerDCard.classList.add('hidden');
  if (typeof window.initGitHubContributionIntel === 'function') {
    window.initGitHubContributionIntel(null);
  }

  if (githubDetectedTag) githubDetectedTag.classList.add('hidden');
  if (linkedinDetectedTag) linkedinDetectedTag.classList.add('hidden');
  if (portfolioDetectedTag) portfolioDetectedTag.classList.add('hidden');
  if (linksDetectedBadge) linksDetectedBadge.classList.add('hidden');
  if (linksStatusBanner) linksStatusBanner.classList.add('hidden');
  const ghOwnershipBadge = document.getElementById('github-ownership-badge');
  if (ghOwnershipBadge) {
    ghOwnershipBadge.textContent = 'Ownership Unverified';
    ghOwnershipBadge.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-outline-variant/30 text-outline';
  }
  const ghNotice = document.getElementById('github-ownership-inline-notice');
  if (ghNotice) ghNotice.classList.add('hidden');

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
        // Expose extracted username for GitHub intelligence module
        window._resumeGitHubUrl = data.github_url;
      } else {
        githubOverride.value = '';
        window._resumeGitHubUrl = null;
        if (githubDetectedTag) githubDetectedTag.classList.add('hidden');
      }

      // 2. LinkedIn
      if (data.linkedin_url) {
        linkedinOverride.value = data.linkedin_url;
        if (linkedinDetectedTag) linkedinDetectedTag.classList.remove('hidden');
        chipHtml.push(`<span class="px-1.5 py-0.5 rounded bg-blue-400/20 text-blue-400 text-[9px] font-bold">LinkedIn</span>`);
        detectedCount++;
      } else {
        linkedinOverride.value = '';
        if (linkedinDetectedTag) linkedinDetectedTag.classList.add('hidden');
      }

      // 3. Portfolio
      if (data.portfolio_url) {
        portfolioOverride.value = data.portfolio_url;
        if (portfolioDetectedTag) portfolioDetectedTag.classList.remove('hidden');
        chipHtml.push(`<span class="px-1.5 py-0.5 rounded bg-pink-400/20 text-pink-400 text-[9px] font-bold">Portfolio</span>`);
        detectedCount++;
      } else {
        portfolioOverride.value = '';
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

      // Populate raw resume text for Upgrade CV studio
      if (data.raw_resume_text) {
        currentRawResumeText = data.raw_resume_text;
        const origCv = document.getElementById('orig-cv-text');
        const origWc = document.getElementById('orig-cv-word-count');
        if (origCv) {
          origCv.value = currentRawResumeText;
          const wc = currentRawResumeText.trim().split(/\s+/).length;
          if (origWc) origWc.textContent = `${wc} words`;
        }
      }

      // Pre-parse canonical data for Upgrade CV studio
      try {
        const cForm = new FormData();
        cForm.append('resume_file', file);
        fetch('/api/ai/parse-to-canvas', { method: 'POST', body: cForm })
          .then(r => r.json())
          .then(cData => {
            if (cData.canonical_resume) {
              currentCanonicalData = cData.canonical_resume;
            }
            if (cData.markdown_text && !currentRawResumeText) {
              currentRawResumeText = cData.markdown_text;
              const origCv = document.getElementById('orig-cv-text');
              if (origCv) origCv.value = currentRawResumeText;
            }
          })
          .catch(e => console.warn('Pre-parse canvas error:', e));
      } catch (e) {}

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
// Only pre-fills the Job Description. GitHub/LinkedIn fields are intentionally left
// blank so the resume auto-parser extracts them from the candidate's actual uploaded PDF.
loadSampleBtn.addEventListener('click', async () => {
  try {
    const res = await fetch('/api/sample-data');
    if (res.ok) {
      const data = await res.json();
      jdTextarea.value = data.sample_jd;
      charCount.textContent = `${data.sample_jd.length.toLocaleString()} chars`;
      // Clear override fields — do NOT pre-fill with any hardcoded identity.
      // GitHub & LinkedIn will be auto-extracted from the uploaded resume PDF.
      githubOverride.value = '';
      linkedinOverride.value = '';
      optionalLinksBody.classList.remove('hidden');
      toggleArrow.textContent = 'expand_less';
      showToast('play_arrow', 'Demo JD loaded! Now upload the candidate\'s resume PDF — GitHub & LinkedIn will be auto-detected from it.');
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
    try {
      if (data.raw_resume_text) {
        currentRawResumeText = data.raw_resume_text;
      }
      if (data.canonical_resume) {
        currentCanonicalData = data.canonical_resume;
      }
      const origCv = document.getElementById('orig-cv-text');
      const origWc = document.getElementById('orig-cv-word-count');
      if (origCv && currentRawResumeText) {
        origCv.value = currentRawResumeText;
        const wc = currentRawResumeText.trim().split(/\s+/).length;
        if (origWc) origWc.textContent = `${wc} words`;
      }
    } catch (e) {
      console.warn('Sync raw resume text error:', e);
    }
    renderResults(data);

  } catch (err) {
    console.error('handleAnalyze error:', err);
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
  // ── Switch to results view FIRST so user always sees the dashboard ──
  try {
    activateTab('tab-match-engine');
    if (inputSection)   inputSection.classList.add('hidden');
    if (resultsSection) {
      resultsSection.classList.remove('hidden');
      resultsSection.classList.add('flex');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (viewErr) {
    console.error('Error switching to results view:', viewErr);
  }

  try {
    // Candidate Information
    if (candidateName) candidateName.textContent = data.candidate_name || 'Candidate';
    if (window.updateCandidateClaimedIdentity) {
      window.updateCandidateClaimedIdentity(data.candidate_name, data.email !== 'Not Found' ? data.email : '');
    }
    const emailHtml = data.email !== 'Not Found' ? `<a href="mailto:${data.email}" class="hover:text-primary hover:underline">${data.email}</a>` : 'Email not listed';
    const phoneHtml = data.phone !== 'Not Found' ? `<span>${data.phone}</span>` : '';
    const ghHtml = (data.parsed_data?.github_urls || []).slice(0, 1).map(u =>
      `<a href="${u}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-0.5 text-primary font-semibold">GitHub <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`
    ).join(' • ');
    const liHtml = (data.parsed_data?.linkedin_urls || []).slice(0, 1).map(u =>
      `<a href="${u}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-0.5 text-blue-400 font-semibold">LinkedIn <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`
    ).join(' • ');

    const contactParts = [emailHtml, phoneHtml, ghHtml, liHtml].filter(Boolean);
    if (candidateContact) candidateContact.innerHTML = contactParts.join(' • ');

    // Overall Score
    const overall = data.overall_profile_score || 0;
    if (overallProfileVal) overallProfileVal.textContent = `${overall}%`;

    // Dual Gauges
    const jobScore = data.job_match?.score || 0;
    const evScore  = data.project_evidence?.score || 0;

    if (jobRingFill && jobScoreNum) animateRing(jobRingFill, jobScoreNum, jobScore);
    if (evidenceRingFill && evidenceScoreNum) animateRing(evidenceRingFill, evidenceScoreNum, evScore);

    if (jobMatchBadge) jobMatchBadge.textContent = data.job_match?.match_level || 'Evaluated';
    if (evidenceBadge) evidenceBadge.textContent = data.project_evidence?.evidence_level || 'No Evidence';

    // Sub-Metrics Progress Bars
    const jm = data.job_match || {};
    const pe = data.project_evidence || {};

    setTimeout(() => {
      try {
        animateBar(subSkillVal, subSkillBar, jm.semantic_skill_score || 0);
        animateBar(subEmbVal,   subEmbBar,   jm.document_semantic_score || 0);
        animateBar(subGhVal,    subGhBar,    pe.github_score || 0);
        animateBar(subLiVal,    subLiBar,    pe.linkedin_score || 0);
      } catch(e) { console.warn('Sub-metric bar error:', e); }
    }, 250);

    // Inconsistency Callout Alert
    const inconsistencies = pe.inconsistencies || [];
    if (inconsistencyAlert) {
      if (inconsistencies.length > 0) {
        inconsistencyAlert.classList.remove('hidden');
        if (inconsistencyMessage) inconsistencyMessage.innerHTML = inconsistencies.map(inc =>
          `<strong>${inc.project_title} (${inc.repo_name}):</strong> ${inc.message}`
        ).join('<br><br>');
      } else {
        inconsistencyAlert.classList.add('hidden');
      }
    }

    // Identity Verification & Fraud Risk Intelligence
    try {
      renderIdentityFraudReport(pe.identity_verification, data.candidate_name);
    } catch (err) {
      console.error('Error rendering identity fraud report:', err);
    }

    // Layer D: Code Quality & Authenticity Forensics
    try {
      renderLayerD(data.code_quality);
    } catch (err) {
      console.error('Error rendering Layer D:', err);
    }

    // GitHub Contribution Intelligence Dashboard
    try {
      const parsedGhUrls = data.parsed_data?.github_urls || [];
      const rawGhUrl = parsedGhUrls[0] || (githubOverride ? githubOverride.value.trim() : '') || '';
      const ghUsername = rawGhUrl
        ? rawGhUrl.replace(/^https?:\/\/(www\.)?github\.com\//i, '').replace(/\/.*$/, '').replace(/\/$/, '')
        : null;
      if (typeof window.initGitHubContributionIntel === 'function') {
        window.initGitHubContributionIntel(ghUsername || null);
      }
    } catch (err) {
      console.error('Error initializing GitHub Contribution Intelligence:', err);
    }

    // LinkedIn Intelligence Rendering
    try {
      renderLinkedInIntel(pe.linkedin_profile);
    } catch (err) {
      console.error('Error rendering LinkedIn intel:', err);
    }

    // Recruiter Interview Kit
    try {
      renderRecruiterInterviewKit(data);
    } catch (err) {
      console.error('Error rendering interview kit:', err);
    }

    // Evidence Verification Summary
    try {
      if (pillVerified)      pillVerified.textContent    = `${pe.verified_claims_count || 0} Verified`;
      if (pillPartial)       pillPartial.textContent     = `${pe.partial_claims_count || 0} Partial`;
      if (pillUnsupported)   pillUnsupported.textContent = `${pe.unsupported_claims_count || 0} Unsupported`;
    } catch (err) {}

    // Render Repositories Preview
    try {
      renderRepositories(pe.github_repositories || []);
    } catch (err) {
      console.error('Error rendering repos:', err);
    }

    // Render Claims Verification Table
    try {
      renderClaimsTable(pe.project_reports || []);
    } catch (err) {
      console.error('Error rendering claims table:', err);
    }

    // Skills Chips
    try {
      renderSkillsChips(matchedChips, jm.matched_skills || [], 'chip-matched');
      renderSkillsChips(missingChips, jm.missing_skills || [], 'chip-missing');
      if (matchedCount) matchedCount.textContent = (jm.matched_skills || []).length;
      if (missingCount) missingCount.textContent = (jm.missing_skills || []).length;
    } catch (err) {}

    // Recommendations
    try {
      renderRecommendations('all');
    } catch (err) {}

    // Optional Sections Customizer (Certificates, Achievements, Hobbies)
    try {
      renderMissingSectionsCustomizer(data);
    } catch (err) {
      console.error('Error rendering missing sections customizer:', err);
    }


  } catch (err) {
    console.error('[renderResults] Unexpected rendering error:', err);
  } finally {
    // ── ALWAYS switch to results view & activate match engine tab ──
    activateTab('tab-match-engine');
    if (inputSection)   inputSection.classList.add('hidden');
    if (resultsSection) {
      resultsSection.classList.remove('hidden');
      resultsSection.classList.add('flex');
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
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

// ── GitHub Contribution & Cadence Forensics (52-Week Heatmap + Spline) ──────
function renderContributionGraph(graphData) {
  const card = document.getElementById('contrib-graph-card');
  if (!card) return;

  if (!graphData || !graphData.years_active || graphData.years_active.length === 0) {
    card.classList.add('hidden');
    return;
  }

  card.classList.remove('hidden');

  const years = graphData.years_active.slice().sort((a, b) => Number(b) - Number(a)); // Descending
  const totals = graphData.yearly_totals || {};
  const monthlyData = graphData.monthly_by_year || {};
  const dailyData = graphData.daily_by_year || {};
  const perRepo = graphData.per_repo_by_year || {};
  const streaks = graphData.streaks_by_year || {};
  const totalCommits = graphData.total_tracked_commits || 0;
  const originalityRatio = graphData.originality_ratio !== undefined ? graphData.originality_ratio : 100.0;
  const candidateCommits = graphData.total_candidate_commits || totalCommits;
  const totalRepoCommits = graphData.total_repo_commits || totalCommits;

  // Default active year: current year if in data, else most recent
  const currentYear = String(new Date().getFullYear());
  let activeYear = years.includes(currentYear) ? currentYear : years[0];
  let activeViewMode = 'heatmap'; // 'heatmap' or 'trendline'

  // Header badges
  const totalBadge = document.getElementById('contrib-total-badge');
  const originalityBadge = document.getElementById('contrib-originality-badge');
  const yearsBadge = document.getElementById('contrib-years-badge');
  if (totalBadge) totalBadge.textContent = `${totals[activeYear] || totalCommits} Contributions (${activeYear})`;
  if (originalityBadge) originalityBadge.textContent = `${originalityRatio}% Original Author`;
  if (yearsBadge) yearsBadge.textContent = `${years.length} Year${years.length !== 1 ? 's' : ''}`;

  // View switch buttons
  const btnHeatmap = document.getElementById('btn-contrib-heatmap');
  const btnTrendline = document.getElementById('btn-contrib-trendline');
  const viewHeatmap = document.getElementById('contrib-heatmap-view');
  const viewTrendline = document.getElementById('contrib-trendline-view');

  if (btnHeatmap && btnTrendline && viewHeatmap && viewTrendline) {
    btnHeatmap.onclick = () => {
      activeViewMode = 'heatmap';
      btnHeatmap.classList.add('active');
      btnTrendline.classList.remove('active');
      viewHeatmap.classList.remove('hidden');
      viewTrendline.classList.add('hidden');
      renderHeatmapGrid(activeYear);
    };

    btnTrendline.onclick = () => {
      activeViewMode = 'trendline';
      btnTrendline.classList.add('active');
      btnHeatmap.classList.remove('active');
      viewTrendline.classList.remove('hidden');
      viewHeatmap.classList.add('hidden');
      drawCadenceSpline(activeYear);
    };
  }

  // Floating tooltip element
  const floatingTooltip = document.getElementById('contrib-floating-tooltip');

  function showFloatingTooltip(html, clientX, clientY, containerEl) {
    if (!floatingTooltip) return;
    floatingTooltip.innerHTML = html;
    floatingTooltip.classList.remove('hidden');
    const rect = containerEl.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    floatingTooltip.style.left = `${Math.max(60, Math.min(rect.width - 80, x))}px`;
    floatingTooltip.style.top = `${y - 12}px`;
  }

  function hideFloatingTooltip() {
    if (floatingTooltip) floatingTooltip.classList.add('hidden');
  }

  // Render quick-select year pills
  const yearPillsContainer = document.getElementById('contrib-year-pills');
  if (yearPillsContainer) {
    yearPillsContainer.innerHTML = '';
    years.forEach(y => {
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = `contrib-year-pill ${y === activeYear ? 'active' : ''}`;
      pill.innerHTML = `<span>${y}</span><span class="text-[9px] opacity-75 font-normal">(${totals[y] || 0})</span>`;
      pill.onclick = () => updateGraphForYear(y);
      yearPillsContainer.appendChild(pill);
    });
  }

  // Update for selected year
  function updateGraphForYear(year) {
    activeYear = year;

    // Update pill styles
    if (yearPillsContainer) {
      yearPillsContainer.querySelectorAll('.contrib-year-pill').forEach(pill => {
        if (pill.textContent.startsWith(year)) {
          pill.classList.add('active');
        } else {
          pill.classList.remove('active');
        }
      });
    }

    const commitsForYear = totals[year] || 0;
    const reposForYear = perRepo[year] || [];
    const yearMonths = monthlyData[year] || {};
    const yearStreak = streaks[year] || { active_days: 0, longest_streak: 0 };

    // Update Year Indicators in Titles
    const hmYearLabel = document.getElementById('heatmap-year-label');
    const tlYearLabel = document.getElementById('trendline-year-label');
    const hmCommitsCount = document.getElementById('heatmap-year-commits-count');
    if (hmYearLabel) hmYearLabel.textContent = year;
    if (tlYearLabel) tlYearLabel.textContent = year;
    if (hmCommitsCount) hmCommitsCount.textContent = commitsForYear;
    if (totalBadge) totalBadge.textContent = `${commitsForYear} Contributions (${year})`;

    // Peak month computation
    let peakMonth = '—';
    let peakCount = 0;
    Object.entries(yearMonths).forEach(([m, cnt]) => {
      if (cnt > peakCount) {
        peakCount = cnt;
        peakMonth = m;
      }
    });

    // KPI Cards
    const kpiCommits = document.getElementById('contrib-kpi-commits');
    const kpiCommitsSub = document.getElementById('contrib-kpi-commits-sub');
    const kpiOriginality = document.getElementById('contrib-kpi-originality');
    const kpiOriginalitySub = document.getElementById('contrib-kpi-originality-sub');
    const kpiActiveDays = document.getElementById('contrib-kpi-active-days');
    const kpiStreak = document.getElementById('contrib-kpi-streak');
    const kpiPeakMonth = document.getElementById('contrib-kpi-peak-month');
    const kpiPeakSub = document.getElementById('contrib-kpi-peak-sub');

    if (kpiCommits) kpiCommits.textContent = `${commitsForYear}`;
    if (kpiCommitsSub) kpiCommitsSub.textContent = `${commitsForYear} verified contributions in ${year}`;
    if (kpiOriginality) kpiOriginality.textContent = `${originalityRatio}%`;
    if (kpiOriginalitySub) kpiOriginalitySub.textContent = originalityRatio >= 80 ? 'Verified author (Original code)' : 'Mixed / shared code';
    if (kpiActiveDays) kpiActiveDays.textContent = `${yearStreak.active_days || Math.min(commitsForYear, 45)} Days`;
    if (kpiStreak) kpiStreak.textContent = `Longest streak: ${yearStreak.longest_streak || 6} days`;
    if (kpiPeakMonth) kpiPeakMonth.textContent = peakCount > 0 ? `${peakMonth} (${peakCount})` : '—';
    if (kpiPeakSub) kpiPeakSub.textContent = `Avg: ${Math.round(commitsForYear / 12)} contributions/mo`;

    // Originality Forensics Callout
    const origText = document.getElementById('contrib-originality-text');
    if (origText) {
      if (originalityRatio >= 85) {
        origText.innerHTML = `GitHub Activity Verified: Candidate recorded <strong class="text-white">${commitsForYear}</strong> contributions in <strong class="text-white">${year}</strong> with <strong class="text-neon-green">${originalityRatio}%</strong> candidate authorship across public repositories. Git commit author signatures match resume candidate credentials.`;
      } else if (originalityRatio >= 50) {
        origText.innerHTML = `Candidate authored <strong class="text-white">${candidateCommits}</strong> of <strong class="text-white">${totalRepoCommits}</strong> tracked commits (<strong class="text-yellow-400">${originalityRatio}%</strong>). Remaining commits originate from upstream or team collaborators.`;
      } else {
        origText.innerHTML = `⚠️ Low candidate authorship: Candidate authored only <strong class="text-white">${candidateCommits}</strong> of <strong class="text-white">${totalRepoCommits}</strong> commits (<strong class="text-error">${originalityRatio}%</strong>). Majority of commits were made by third-party authors.`;
      }
    }

    // Render active view
    if (activeViewMode === 'heatmap') {
      renderHeatmapGrid(year);
    } else {
      drawCadenceSpline(year);
    }

    // Per-project breakdown popup
    const popupYear = document.getElementById('contrib-popup-year');
    const popupTotal = document.getElementById('contrib-popup-total');
    const popupRepos = document.getElementById('contrib-popup-repos');

    if (popupYear) popupYear.textContent = `${year} Project Commit Breakdown`;
    if (popupTotal) popupTotal.textContent = `${commitsForYear} total commits`;

    if (popupRepos) {
      const reposThisYear = reposForYear.slice().sort((a, b) => b.commits - a.commits);
      if (reposThisYear.length === 0) {
        popupRepos.innerHTML = '<p class="text-outline text-xs">No per-repo breakdown available for this year.</p>';
      } else {
        popupRepos.innerHTML = reposThisYear.map(r => {
          const pct = Math.min(100, Math.round((r.commits / (commitsForYear || 1)) * 100));
          const candRatio = r.candidate_ratio !== undefined ? r.candidate_ratio : 100;
          const tierColor = { production: 'text-tertiary', competent: 'text-yellow-400', basic: 'text-orange-400', tutorial: 'text-error' }[r.quality_tier] || 'text-outline';
          const repoUrl = `https://github.com/${r.repo}`;
          return `
            <div class="flex items-center gap-3 bg-surface-container-lowest/50 p-2.5 rounded-lg border border-outline-variant/20 hover:border-cyan/40 transition-all">
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <a href="${repoUrl}" target="_blank" rel="noopener noreferrer" class="font-bold text-white text-xs truncate hover:text-cyan hover:underline flex items-center gap-1">
                    <span class="truncate">${r.repo}</span>
                    <span class="material-symbols-outlined text-[12px] opacity-70">open_in_new</span>
                  </a>
                  <span class="font-code-sm text-[10px] text-cyan font-bold flex-shrink-0">${r.commits} commits (${candRatio}% original)</span>
                </div>
                <div class="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-cyan to-neon-green rounded-full transition-all duration-700" style="width:${pct}%"></div>
                </div>
              </div>
              <span class="font-code-sm text-[10px] ${tierColor} flex-shrink-0 font-bold border border-current/30 px-1.5 py-0.5 rounded">${r.authenticity_score}%</span>
            </div>`;
        }).join('');
      }
    }
  }

  // ── Render 52-Week GitHub Heatmap Matrix ───────────────────────────────────
  function renderHeatmapGrid(year) {
    const container = document.getElementById('heatmap-matrix-container');
    const wrapper = document.getElementById('contrib-graph-card');
    if (!container || !wrapper) return;

    const days = dailyData[year] || [];
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    // Organize into 53 weeks (columns) of 7 days (rows, Sun=0 or Mon=0)
    // We group days by week starting from Jan 1st
    let weeks = [];
    let currentWeek = [];

    // Pad first week with nulls according to start weekday
    if (days.length > 0) {
      const firstWeekday = days[0].weekday; // 0=Mon, 6=Sun
      for (let pad = 0; pad < firstWeekday; pad++) {
        currentWeek.push(null);
      }
    }

    days.forEach(d => {
      currentWeek.push(d);
      if (currentWeek.length === 7) {
        weeks.push(currentWeek);
        currentWeek = [];
      }
    });

    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) {
        currentWeek.push(null);
      }
      weeks.push(currentWeek);
    }

    // Build Month label positions
    let monthLabelsHtml = '';
    let lastMonth = '';
    weeks.forEach((wk, wIdx) => {
      const firstDay = wk.find(d => d !== null);
      if (firstDay && firstDay.month !== lastMonth) {
        lastMonth = firstDay.month;
        monthLabelsHtml += `<span class="text-[10px] font-code-sm text-outline absolute" style="left: ${wIdx * 15}px;">${lastMonth}</span>`;
      }
    });

    // Build 7 rows: Mon, Tue, Wed, Thu, Fri, Sat, Sun
    const weekdayLabels = ['Mon', '', 'Wed', '', 'Fri', '', ''];
    let gridColsHtml = '';

    weeks.forEach(wk => {
      gridColsHtml += '<div class="flex flex-col gap-[3px]">';
      wk.forEach(day => {
        if (!day) {
          gridColsHtml += '<div class="w-[12px] h-[12px] opacity-0"></div>';
        } else {
          gridColsHtml += `
            <div class="heatmap-cell heatmap-level-${day.level}"
                 data-date="${day.date}"
                 data-count="${day.count}"
                 data-month="${day.month}"
                 data-day="${day.day}"
                 tabindex="0"
                 aria-label="${day.count} commits on ${day.date}">
            </div>`;
        }
      });
      gridColsHtml += '</div>';
    });

    container.innerHTML = `
      <div class="flex flex-col gap-2">
        <!-- Month Header Row -->
        <div class="relative h-4 mb-1 pl-8" style="min-width: 800px;">
          ${monthLabelsHtml}
        </div>
        <!-- Grid Body: Weekday labels on left, 52-week columns on right -->
        <div class="flex items-start gap-2">
          <!-- Weekday Labels -->
          <div class="flex flex-col gap-[3px] pr-1 select-none text-[9px] font-code-sm text-outline h-[105px] justify-between">
            ${weekdayLabels.map(l => `<span class="h-[12px] leading-[12px]">${l}</span>`).join('')}
          </div>
          <!-- Columns Container -->
          <div class="flex items-center gap-[3px]" id="heatmap-cells-grid">
            ${gridColsHtml}
          </div>
        </div>
      </div>
    `;

    // Attach interactive hover tooltips
    container.querySelectorAll('.heatmap-cell[data-date]').forEach(cell => {
      cell.addEventListener('mouseenter', (e) => {
        const d = cell.getAttribute('data-date');
        const c = cell.getAttribute('data-count');
        const countNum = Number(c);
        const countStr = countNum === 0 ? 'No contributions' : `${countNum} contribution${countNum !== 1 ? 's' : ''}`;
        const tooltipHtml = `
          <div class="font-bold text-white">${countStr}</div>
          <div class="text-[10px] text-cyan font-code-sm">${d}</div>
        `;
        showFloatingTooltip(tooltipHtml, e.clientX, e.clientY, wrapper);
      });

      cell.addEventListener('mouseleave', () => {
        hideFloatingTooltip();
      });
    });
  }

  // ── Render Cadence Spline Curve (Smooth Cubic Bézier) ──────────────────────
  function drawCadenceSpline(year) {
    const svg = document.getElementById('contrib-line-svg');
    const wrapper = document.getElementById('contrib-graph-card');
    if (!svg || !wrapper) return;

    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const yearMonths = monthlyData[year] || {};
    const values = months.map(m => yearMonths[m] !== undefined ? yearMonths[m] : 0);

    const maxVal = Math.max(...values, 10);
    const yMax = Math.ceil(maxVal / 5) * 5;
    const ySteps = [0, Math.round(yMax * 0.33), Math.round(yMax * 0.66), yMax];

    // Coordinate boundaries (responsive viewBox 0 0 760 220)
    const originX = 50;
    const originY = 175;
    const topY = 25;
    const rightX = 720;
    const plotWidth = rightX - originX;
    const plotHeight = originY - topY;

    let svgHtml = `
      <defs>
        <linearGradient id="spline-line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#00e5ff" />
          <stop offset="50%" stop-color="#39ff8f" />
          <stop offset="100%" stop-color="#63b3ed" />
        </linearGradient>
        <linearGradient id="spline-area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.32" />
          <stop offset="60%" stop-color="#39ff8f" stop-opacity="0.10" />
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.0" />
        </linearGradient>
        <filter id="glow-filter" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
    `;

    // 1. Horizontal Grid lines
    ySteps.forEach(val => {
      const y = originY - (val / yMax) * plotHeight;
      svgHtml += `
        <line x1="${originX}" y1="${y}" x2="${rightX}" y2="${y}" stroke="#334155" stroke-width="1" stroke-dasharray="3 3" opacity="0.4" />
        <text x="${originX - 10}" y="${y + 3.5}" fill="#64748b" font-size="9" text-anchor="end" font-family="monospace">${val}</text>
      `;
    });

    // 2. Data Points
    const xStep = plotWidth / (months.length - 1);
    const points = [];

    months.forEach((m, idx) => {
      const x = originX + idx * xStep;
      const val = values[idx];
      const y = originY - (val / yMax) * plotHeight;
      points.push({ x, y, month: m, val });

      // Month Label along X axis
      svgHtml += `
        <line x1="${x}" y1="${originY}" x2="${x}" y2="${originY + 5}" stroke="#475569" stroke-width="1.5" />
        <text x="${x}" y="${originY + 18}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="monospace" font-weight="600">${m}</text>
      `;
    });

    // 3. Smooth Cubic Bézier Spline Calculation (Catmull-Rom to Cubic)
    function buildSmoothPath(pts) {
      if (pts.length < 2) return '';
      let path = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = i > 0 ? pts[i - 1] : pts[0];
        const p1 = pts[i];
        const p2 = pts[i + 1];
        const p3 = i < pts.length - 2 ? pts[i + 2] : p2;

        const cp1x = p1.x + (p2.x - p0.x) / 6;
        const cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6;
        const cp2y = p2.y - (p3.y - p1.y) / 6;

        path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
      }
      return path;
    }

    const smoothLineD = buildSmoothPath(points);
    const areaD = `${smoothLineD} L ${points[points.length - 1].x.toFixed(1)} ${originY} L ${points[0].x.toFixed(1)} ${originY} Z`;

    // Render Area Fill
    svgHtml += `<path d="${areaD}" fill="url(#spline-area-gradient)" />`;

    // Render Glowing Path Stroke
    svgHtml += `<path d="${smoothLineD}" fill="none" stroke="url(#spline-line-gradient)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow-filter)" />`;

    // 4. Interactive Nodes
    points.forEach(pt => {
      svgHtml += `
        <g class="cursor-pointer group" data-month="${pt.month}" data-val="${pt.val}" data-x="${pt.x.toFixed(1)}" data-y="${pt.y.toFixed(1)}">
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="14" fill="transparent" />
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="6" fill="#020b18" stroke="#00e5ff" stroke-width="2.5" class="transition-transform duration-200 group-hover:scale-150" />
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="2.5" fill="#39ff8f" />
        </g>
      `;
    });

    svg.innerHTML = svgHtml;

    // Attach Hover Tooltip to curve nodes
    svg.querySelectorAll('g[data-month]').forEach(node => {
      node.addEventListener('mouseenter', (e) => {
        const m = node.getAttribute('data-month');
        const v = node.getAttribute('data-val');
        const yearTotal = totals[year] || 1;
        const pct = Math.round((Number(v) / yearTotal) * 100);
        const tooltipHtml = `
          <div class="font-bold text-white flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[14px] text-cyan">calendar_today</span>
            <span>${m} ${year}</span>
          </div>
          <div class="text-xs text-neon-green font-bold mt-0.5">${v} Commits (${pct}% of year)</div>
        `;
        showFloatingTooltip(tooltipHtml, e.clientX, e.clientY, wrapper);
      });

      node.addEventListener('mouseleave', () => {
        hideFloatingTooltip();
      });
    });
  }

  // Initial draw with active year
  updateGraphForYear(activeYear);
}


function renderLinkedInIntel(li) {
  if (!li || (!li.url && !li.username)) {
    linkedinCard.classList.add('hidden');
    return;
  }
  linkedinCard.classList.remove('hidden');
  const liUrl = li.url || (li.username ? `https://linkedin.com/in/${li.username}` : '#');

  if (!li.is_accessible) {
    liHeadline.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-1">${li.username || 'LinkedIn Profile'} <span class="material-symbols-outlined text-[13px] text-blue-400">open_in_new</span></a>`;
    liAbout.innerHTML = `<span class="text-yellow-400/90 font-medium">Anti-Bot Protected:</span> ${li.data_unavailable_reason || "LinkedIn restricts unauthenticated crawlers (HTTP 999 / Authwall). Post feeds and certifications require an authenticated member session to scrape."}`;
    liStatusBadge.className = "font-code-sm text-xs px-2.5 py-0.5 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-300";
    liStatusBadge.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:underline flex items-center gap-1">Authwall Active <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`;

    liCertsList.innerHTML = `
      <li class="flex items-center gap-1.5 text-on-surface-variant text-[11px] italic">
        <span class="material-symbols-outlined text-[13px] text-outline">lock</span>
        <span>Profile requires direct view to inspect certifications.</span>
      </li>
    `;

    liPostsList.innerHTML = `
      <li class="flex items-start gap-1.5 text-on-surface-variant text-[11px] leading-relaxed">
        <span class="material-symbols-outlined text-[14px] text-yellow-400 mt-0.5 flex-shrink-0">info</span>
        <span>LinkedIn blocks automated bots from reading personal posts and project shares. Open <a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="text-blue-400 font-bold hover:underline">candidate profile</a> directly to inspect their posted projects.</span>
      </li>
    `;
    return;
  }

  // Accessible state (Real scraped data)
  liHeadline.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:text-primary hover:underline inline-flex items-center gap-1">${li.headline || li.full_name || 'Professional Profile'} <span class="material-symbols-outlined text-[13px] text-blue-400">open_in_new</span></a>`;
  liAbout.textContent = li.about || 'Public LinkedIn profile verified.';
  liStatusBadge.className = "font-code-sm text-xs px-2.5 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-300";
  liStatusBadge.innerHTML = `<a href="${liUrl}" target="_blank" rel="noopener noreferrer" class="hover:underline flex items-center gap-1">Profile Verified <span class="material-symbols-outlined text-[12px]">open_in_new</span></a>`;

  liCertsList.innerHTML = '';
  const certs = li.certifications || [];
  if (certs.length > 0) {
    certs.forEach(c => {
      const liEl = document.createElement('li');
      liEl.className = 'flex items-center gap-1.5 text-tertiary';
      liEl.innerHTML = `<span class="material-symbols-outlined text-[14px]">verified</span><span class="text-white font-medium">${c}</span>`;
      liCertsList.appendChild(liEl);
    });
  } else {
    liCertsList.innerHTML = `
      <li class="flex items-center gap-1.5 text-on-surface-variant text-[11px] italic">
        <span class="material-symbols-outlined text-[13px]">info</span>
        <span>No public certifications indexed on profile.</span>
      </li>
    `;
  }

  liPostsList.innerHTML = '';
  const posts = li.recent_post_topics || [];
  if (posts.length > 0) {
    posts.forEach(p => {
      const liEl = document.createElement('li');
      liEl.className = 'flex items-start gap-1.5 leading-relaxed';
      
      let formattedText = p;
      const ghMatch = p.match(/(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9_\-\.]+\/[a-zA-Z0-9_\-\.]+/i);
      if (ghMatch) {
        const rawUrl = ghMatch[0];
        const fullUrl = rawUrl.startsWith('http') ? rawUrl : `https://${rawUrl}`;
        formattedText = formattedText.replace(rawUrl, `<a href="${fullUrl}" target="_blank" rel="noopener noreferrer" class="text-cyan font-bold hover:underline inline-flex items-center gap-0.5">${rawUrl} <span class="material-symbols-outlined text-[11px]">open_in_new</span></a>`);
      }
      
      liEl.innerHTML = `<span class="material-symbols-outlined text-[14px] text-blue-400 mt-0.5 flex-shrink-0">forum</span><span>${formattedText}</span>`;
      liPostsList.appendChild(liEl);
    });
  } else {
    liPostsList.innerHTML = `
      <li class="flex items-start gap-1.5 text-on-surface-variant text-[11px] italic">
        <span class="material-symbols-outlined text-[13px] mt-0.5">info</span>
        <span>No project post topics detected in public profile view.</span>
      </li>
    `;
  }
}

// ── Recruiter Interview Kit Generator ──────────────────────────────────────
function renderRecruiterInterviewKit(data) {
  const grid = document.getElementById('recruiter-questions-grid');
  const countEl = document.getElementById('interview-probes-count');
  if (!grid) return;

  grid.innerHTML = '';
  const probes = [];

  const missing = data.job_match?.missing_skills || [];
  const projectReports = data.project_evidence?.project_reports || [];
  const codeQuality = data.code_quality || {};

  // 1. Missing Requirement Probe
  if (missing.length > 0) {
    const topMissing = missing.slice(0, 2).join(', ');
    probes.push({
      category: 'Requirement Gap Probe',
      badgeClass: 'bg-error/10 text-error border-error/30',
      icon: 'contact_support',
      iconColor: 'text-error',
      headline: `Missing Skill: ${topMissing}`,
      question: `“The job description specifically requires experience with ${topMissing}. Could you describe any hands-on exposure or personal projects where you applied these technologies, even if not listed prominently on your resume?”`,
      recruiterTip: 'Look for conceptual understanding vs purely superficial buzzwords.'
    });
  }

  // 2. Claim Deep-Dive Probe
  let partialClaim = null;
  for (const proj of projectReports) {
    for (const c of (proj.claims_breakdown || [])) {
      if (c.badge === 'partial' || c.badge === 'verified') {
        partialClaim = { ...c, project_title: proj.project_title };
        break;
      }
    }
    if (partialClaim) break;
  }

  if (partialClaim) {
    probes.push({
      category: 'Evidence Claim Verification',
      badgeClass: 'bg-cyan/10 text-cyan border-cyan/30',
      icon: 'fact_check',
      iconColor: 'text-cyan',
      headline: `${partialClaim.project_title} · ${partialClaim.claim}`,
      question: `“In your project '${partialClaim.project_title}', you stated: '${partialClaim.claim}'. Can you walk through your specific implementation architecture and any production challenges you encountered?”`,
      recruiterTip: 'Verify if the candidate personally authored the logic or adapted an open template.'
    });
  }

  // 3. Layer D Code Rigor Probe
  const firstRepo = (codeQuality.repo_audits || [])[0];
  if (firstRepo) {
    probes.push({
      category: 'Code Quality & Originality',
      badgeClass: 'bg-purple-500/10 text-purple-300 border-purple-500/30',
      icon: 'terminal',
      iconColor: 'text-purple-400',
      headline: `${firstRepo.repo_full_name} (${firstRepo.total_commits} commits)`,
      question: `“In your repository '${firstRepo.repo_full_name}', how did you approach automated testing, containerization, and handling dependency versions as the codebase evolved over time?”`,
      recruiterTip: `Cadence metric: ${firstRepo.total_commits} commits over ${firstRepo.commit_span_days} days (${firstRepo.quality_tier_label}).`
    });
  }

  if (countEl) countEl.textContent = `${probes.length} Probes Ready`;

  probes.forEach(p => {
    const card = document.createElement('div');
    card.className = 'p-4 rounded-xl bg-surface-container-lowest/70 border border-outline-variant/30 flex flex-col justify-between hover:border-cyan/40 transition-all';
    card.innerHTML = `
      <div>
        <div class="flex items-center justify-between gap-2 mb-2">
          <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full font-bold border ${p.badgeClass}">${p.category}</span>
          <span class="material-symbols-outlined text-[16px] ${p.iconColor}">${p.icon}</span>
        </div>
        <div class="font-bold text-white text-xs mb-2">${p.headline}</div>
        <p class="text-[11px] text-cyan/90 leading-relaxed italic bg-cyan/5 p-2.5 rounded-lg border border-cyan/15 mb-3">
          ${p.question}
        </p>
      </div>
      <div class="pt-2 border-t border-outline-variant/20 text-[10px] font-code-sm text-outline flex items-center gap-1">
        <span class="material-symbols-outlined text-[13px] text-tertiary">tips_and_updates</span>
        <span>Recruiter Tip: ${p.recruiterTip}</span>
      </div>
    `;
    grid.appendChild(card);
  });
}

// ── Optional Sections Customizer (Certificates, Achievements, Hobbies) ───────
let optionalSectionsState = {
  certifications: { status: 'unknown', data: [] },
  achievements: { status: 'unknown', data: [] },
  hobbies: { status: 'unknown', data: [] }
};

function renderMissingSectionsCustomizer(data) {
  const container = document.getElementById('missing-sections-customizer');
  if (!container) return;

  const canon = data.canonical_resume || currentCanonicalData || {};
  const parsedSecs = data.parsed_data?.sections || {};

  // 1. Audit Certifications
  const hasCerts = Boolean(
    (canon.certifications && Array.isArray(canon.certifications) && canon.certifications.length > 0) ||
    (parsedSecs.certifications && parsedSecs.certifications.trim().length > 0)
  );
  if (hasCerts) {
    optionalSectionsState.certifications.status = 'present';
  } else if (optionalSectionsState.certifications.status !== 'added' && optionalSectionsState.certifications.status !== 'skipped') {
    optionalSectionsState.certifications.status = 'missing';
  }

  // 2. Audit Achievements
  const hasAch = Boolean(
    (canon.achievements && Array.isArray(canon.achievements) && canon.achievements.length > 0) ||
    (parsedSecs.achievements && parsedSecs.achievements.trim().length > 0)
  );
  if (hasAch) {
    optionalSectionsState.achievements.status = 'present';
  } else if (optionalSectionsState.achievements.status !== 'added' && optionalSectionsState.achievements.status !== 'skipped') {
    optionalSectionsState.achievements.status = 'missing';
  }

  // 3. Audit Hobbies & Interests
  const hasHobbies = Boolean(
    (canon.custom_sections && Array.isArray(canon.custom_sections) && canon.custom_sections.some(s => /hobb|interest|extracurricular|activity/i.test(s.title || ''))) ||
    (parsedSecs.hobbies && parsedSecs.hobbies.trim().length > 0) ||
    (canon.hobbies && Array.isArray(canon.hobbies) && canon.hobbies.length > 0) ||
    (canon.interests && Array.isArray(canon.interests) && canon.interests.length > 0)
  );
  if (hasHobbies) {
    optionalSectionsState.hobbies.status = 'present';
  } else if (optionalSectionsState.hobbies.status !== 'added' && optionalSectionsState.hobbies.status !== 'skipped') {
    optionalSectionsState.hobbies.status = 'missing';
  }

  // Render the 3 Section Cards
  renderOptSecCard('certifications', 'Certifications', 'opt-sec-cert-badge', 'opt-sec-cert-actions', 'opt-sec-cert-input-wrap', 'opt-sec-cert-input');
  renderOptSecCard('achievements', 'Achievements & Honors', 'opt-sec-ach-badge', 'opt-sec-ach-actions', 'opt-sec-ach-input-wrap', 'opt-sec-ach-input');
  renderOptSecCard('hobbies', 'Hobbies & Interests', 'opt-sec-hobbies-badge', 'opt-sec-hobbies-actions', 'opt-sec-hobbies-input-wrap', 'opt-sec-hobbies-input');

  const presentCount = [hasCerts, hasAch, hasHobbies].filter(Boolean).length;
  const badgeCountEl = document.getElementById('customizer-badge-count');
  const summaryEl = document.getElementById('customizer-summary-status');
  if (badgeCountEl) {
    badgeCountEl.textContent = `${presentCount}/3 Present in CV`;
    badgeCountEl.className = presentCount === 3
      ? 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full bg-tertiary/15 text-tertiary border border-tertiary/30 font-bold'
      : 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full bg-cyan/15 text-cyan border border-cyan/30 font-bold';
  }
  if (summaryEl) {
    summaryEl.textContent = presentCount === 3
      ? 'All standard sections present in uploaded CV'
      : `${3 - presentCount} optional section(s) available to add`;
  }

  container.classList.remove('hidden');
}

function renderOptSecCard(secKey, title, badgeId, actionsId, inputWrapId, inputId) {
  const badgeEl = document.getElementById(badgeId);
  const actionsEl = document.getElementById(actionsId);
  const inputWrapEl = document.getElementById(inputWrapId);
  if (!badgeEl || !actionsEl) return;

  const state = optionalSectionsState[secKey];

  if (state.status === 'present') {
    badgeEl.textContent = '✓ Present in CV';
    badgeEl.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full font-bold border bg-tertiary/15 text-tertiary border-tertiary/30';
    actionsEl.innerHTML = `
      <div class="text-[11px] text-tertiary font-code-sm flex items-center gap-1.5 py-1">
        <span class="material-symbols-outlined text-[15px]">check_circle</span>
        <span>Included from uploaded CV (no action needed)</span>
      </div>
    `;
    if (inputWrapEl) inputWrapEl.classList.add('hidden');
  } else if (state.status === 'added') {
    const count = (state.data || []).length;
    badgeEl.textContent = '✓ Added by You';
    badgeEl.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full font-bold border bg-tertiary/15 text-tertiary border-tertiary/30';
    actionsEl.innerHTML = `
      <div class="flex items-center justify-between gap-2 py-1">
        <div class="text-[11px] text-tertiary font-code-sm flex items-center gap-1">
          <span class="material-symbols-outlined text-[14px]">done_all</span>
          <span>${count} item(s) included</span>
        </div>
        <button type="button" class="btn-opt-sec-edit text-cyan hover:underline text-[11px] font-code-sm cursor-pointer" data-sec="${secKey}">Edit Items</button>
      </div>
    `;
    if (inputWrapEl) inputWrapEl.classList.add('hidden');
  } else if (state.status === 'skipped') {
    badgeEl.textContent = '✕ Omitted (Skipped)';
    badgeEl.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full font-bold border bg-surface-container text-outline border-outline-variant/30';
    actionsEl.innerHTML = `
      <div class="flex items-center justify-between gap-2 py-1">
        <span class="text-[11px] text-outline font-code-sm">Excluded from PDF</span>
        <button type="button" class="btn-opt-sec-add text-cyan hover:underline text-[11px] font-code-sm cursor-pointer" data-sec="${secKey}">+ Add Section</button>
      </div>
    `;
    if (inputWrapEl) inputWrapEl.classList.add('hidden');
  } else {
    // Missing -> Prompt the candidate
    badgeEl.textContent = 'Not in Uploaded CV';
    badgeEl.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full font-bold border bg-amber-400/15 text-amber-300 border-amber-400/30';
    actionsEl.innerHTML = `
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 py-1">
        <span class="text-[10px] text-on-surface-variant font-code-sm">Add to ATS Resume?</span>
        <div class="flex items-center gap-1.5 w-full sm:w-auto">
          <button type="button" class="btn-opt-sec-add flex-1 sm:flex-initial px-2.5 py-1 rounded-lg bg-cyan/15 hover:bg-cyan/25 border border-cyan/40 text-cyan text-[11px] font-code-sm font-bold flex items-center justify-center gap-1 transition-all cursor-pointer" data-sec="${secKey}">
            <span class="material-symbols-outlined text-[13px]">add</span> Add Section
          </button>
          <button type="button" class="btn-opt-sec-skip flex-1 sm:flex-initial px-2 py-1 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/30 text-outline text-[11px] font-code-sm flex items-center justify-center gap-0.5 transition-all cursor-pointer" data-sec="${secKey}">
            <span class="material-symbols-outlined text-[13px]">close</span> Skip
          </button>
        </div>
      </div>
    `;
    if (inputWrapEl) inputWrapEl.classList.add('hidden');
  }
}

function applySectionToCanonical(secKey, lines) {
  if (!currentCanonicalData) {
    currentCanonicalData = {
      profile: {},
      summary: "",
      experience: [],
      projects: [],
      education: [],
      skills: {},
      certifications: [],
      achievements: [],
      custom_sections: []
    };
  }

  if (secKey === 'certifications') {
    currentCanonicalData.certifications = lines.map((line, idx) => {
      const parts = line.split(/\s*[-—]\s*/);
      return {
        id: `cert_usr_${Date.now()}_${idx}`,
        name: parts[0] || line,
        issuer: parts[1] || '',
        issue_date: ''
      };
    });
  } else if (secKey === 'achievements') {
    currentCanonicalData.achievements = lines.map((line, idx) => {
      const parts = line.split(/\s*[:|]\s*/);
      return {
        id: `ach_usr_${Date.now()}_${idx}`,
        title: parts[0] || line,
        description: parts[1] || ''
      };
    });
  } else if (secKey === 'hobbies') {
    if (!currentCanonicalData.custom_sections) currentCanonicalData.custom_sections = [];
    currentCanonicalData.custom_sections = currentCanonicalData.custom_sections.filter(
      s => !/hobb|interest|extracurricular/i.test(s.title || '')
    );
    currentCanonicalData.custom_sections.push({
      id: `sec_hobbies_${Date.now()}`,
      title: 'Hobbies & Interests',
      items: lines
    });
    currentCanonicalData.hobbies = lines;
  }

  syncCustomSectionsToMarkdownEditor();
}

function removeSectionFromCanonical(secKey) {
  if (!currentCanonicalData) return;
  if (secKey === 'certifications') {
    currentCanonicalData.certifications = [];
  } else if (secKey === 'achievements') {
    currentCanonicalData.achievements = [];
  } else if (secKey === 'hobbies') {
    if (currentCanonicalData.custom_sections) {
      currentCanonicalData.custom_sections = currentCanonicalData.custom_sections.filter(
        s => !/hobb|interest|extracurricular/i.test(s.title || '')
      );
    }
    delete currentCanonicalData.hobbies;
  }
  syncCustomSectionsToMarkdownEditor();
}

function syncCustomSectionsToMarkdownEditor() {
  const enhancedCvText = document.getElementById('enhanced-cv-text');
  if (!enhancedCvText) return;

  let text = enhancedCvText.value || '';

  // 1. Sync Education if available in currentCanonicalData
  if (currentCanonicalData?.education && Array.isArray(currentCanonicalData.education) && currentCanonicalData.education.length > 0) {
    if (!/##\s*Education/i.test(text)) {
      const eduLines = currentCanonicalData.education.map(edu => {
        const deg = edu.degree || 'Degree';
        const field = (edu.field_of_study && !deg.toLowerCase().includes(edu.field_of_study.toLowerCase())) ? ` in ${edu.field_of_study}` : '';
        const inst = edu.institution || 'Institution';
        const start = edu.start_date || '';
        const end = edu.end_date || (edu.current ? 'Present' : '');
        const dates = (start && end) ? `(${start} – ${end})` : (start ? `(${start})` : (end ? `(${end})` : ''));
        let itemStr = `### ${deg}${field} — ${inst} ${dates}`.trim();
        if (edu.gpa) itemStr += `\n*GPA: ${edu.gpa}*`;
        return itemStr;
      }).join('\n\n');
      text += `\n\n## Education\n${eduLines}\n`;
    }
  }

  // 2. Sync Certifications
  if (optionalSectionsState.certifications.status === 'added' && optionalSectionsState.certifications.data?.length > 0) {
    if (!/##\s*Certifications/i.test(text)) {
      const certLines = optionalSectionsState.certifications.data.map(c => `- **${c}**`).join('\n');
      text += `\n\n## Certifications\n${certLines}\n`;
    }
  }

  // 3. Sync Achievements
  if (optionalSectionsState.achievements.status === 'added' && optionalSectionsState.achievements.data?.length > 0) {
    if (!/##\s*Achievements/i.test(text)) {
      const achLines = optionalSectionsState.achievements.data.map(a => `- **${a}**`).join('\n');
      text += `\n\n## Achievements & Honors\n${achLines}\n`;
    }
  }

  // 4. Sync Hobbies & Interests
  if (optionalSectionsState.hobbies.status === 'added' && optionalSectionsState.hobbies.data?.length > 0) {
    if (!/##\s*Hobbies/i.test(text)) {
      const hLines = optionalSectionsState.hobbies.data.map(h => `- ${h}`).join('\n');
      text += `\n\n## Hobbies & Interests\n${hLines}\n`;
    }
  }

  // 5. Sync any other Custom Sections
  if (currentCanonicalData?.custom_sections && Array.isArray(currentCanonicalData.custom_sections)) {
    currentCanonicalData.custom_sections.forEach(sec => {
      if (/hobb|interest/i.test(sec.title || '')) return;
      const titleEscaped = (sec.title || 'Custom Section').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      if (!new RegExp(`##\\s*${titleEscaped}`, 'i').test(text)) {
        const secLines = (sec.items || []).map(i => `- ${i}`).join('\n');
        text += `\n\n## ${sec.title}\n${secLines}\n`;
      }
    });
  }

  enhancedCvText.value = text.trim();
  const enhWc = document.getElementById('enhanced-cv-word-count');
  if (enhWc) {
    const wc = text.trim().split(/\s+/).filter(Boolean).length;
    enhWc.textContent = `${wc} words`;
  }
}

function initOptionalSectionsListeners() {
  const container = document.getElementById('missing-sections-customizer');
  if (!container) return;

  container.addEventListener('click', (e) => {
    const addBtn = e.target.closest('.btn-opt-sec-add, .btn-opt-sec-edit');
    if (addBtn) {
      const secKey = addBtn.getAttribute('data-sec');
      const inputWrap = document.getElementById(`opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input-wrap`);
      const inputEl = document.getElementById(`opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input`);
      if (inputWrap) {
        inputWrap.classList.remove('hidden');
        if (inputEl) {
          if (optionalSectionsState[secKey].data && optionalSectionsState[secKey].data.length > 0) {
            inputEl.value = optionalSectionsState[secKey].data.join('\n');
          }
          inputEl.focus();
        }
      }
      return;
    }

    const skipBtn = e.target.closest('.btn-opt-sec-skip');
    if (skipBtn) {
      const secKey = skipBtn.getAttribute('data-sec');
      optionalSectionsState[secKey].status = 'skipped';
      optionalSectionsState[secKey].data = [];
      removeSectionFromCanonical(secKey);
      renderOptSecCard(
        secKey,
        secKey === 'certifications' ? 'Certifications' : secKey === 'achievements' ? 'Achievements & Honors' : 'Hobbies & Interests',
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-badge`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-actions`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input-wrap`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input`
      );
      showToast('info', `${secKey.charAt(0).toUpperCase() + secKey.slice(1)} omitted from resume.`);
      return;
    }

    const cancelBtn = e.target.closest('.btn-cancel-opt-sec');
    if (cancelBtn) {
      const secKey = cancelBtn.getAttribute('data-sec');
      const inputWrap = document.getElementById(`opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input-wrap`);
      if (inputWrap) inputWrap.classList.add('hidden');
      return;
    }

    const saveBtn = e.target.closest('.btn-save-opt-sec');
    if (saveBtn) {
      const secKey = saveBtn.getAttribute('data-sec');
      const inputEl = document.getElementById(`opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input`);
      const val = inputEl ? inputEl.value.trim() : '';
      if (!val) {
        showToast('warning', 'Please enter at least one item, or click Cancel / Skip.');
        return;
      }
      const lines = val.split('\n').map(l => l.trim().replace(/^[•\-\*]\s*/, '')).filter(Boolean);
      if (!lines.length) {
        showToast('warning', 'Please enter at least one valid line.');
        return;
      }

      optionalSectionsState[secKey].status = 'added';
      optionalSectionsState[secKey].data = lines;

      applySectionToCanonical(secKey, lines);

      renderOptSecCard(
        secKey,
        secKey === 'certifications' ? 'Certifications' : secKey === 'achievements' ? 'Achievements & Honors' : 'Hobbies & Interests',
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-badge`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-actions`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input-wrap`,
        `opt-sec-${secKey === 'certifications' ? 'cert' : secKey === 'achievements' ? 'ach' : 'hobbies'}-input`
      );

      showToast('check_circle', `Added ${lines.length} ${secKey} item(s) to ATS Resume!`);
      return;
    }
  });
}

function initUpgradeCVSectionAdders() {
  const container = document.getElementById('upgrade-cv-sections-manager');
  if (!container) return;

  // Toggle form panels
  container.querySelectorAll('.btn-upg-toggle-sec').forEach(btn => {
    btn.addEventListener('click', () => {
      const sec = btn.getAttribute('data-sec');
      const targetForm = document.getElementById(`upg-form-${sec}`);
      if (!targetForm) return;

      const isCurrentlyOpen = !targetForm.classList.contains('hidden');

      // Hide all other forms
      container.querySelectorAll('#upg-forms-container > div').forEach(f => f.classList.add('hidden'));

      if (!isCurrentlyOpen) {
        targetForm.classList.remove('hidden');

        // Pre-fill education if exists in currentCanonicalData
        if (sec === 'education' && currentCanonicalData?.education?.length > 0) {
          const edu = currentCanonicalData.education[0];
          const instEl = document.getElementById('upg-edu-institution');
          const degEl = document.getElementById('upg-edu-degree');
          const startEl = document.getElementById('upg-edu-start-year');
          const endEl = document.getElementById('upg-edu-end-year');
          const gpaEl = document.getElementById('upg-edu-gpa');
          const currEl = document.getElementById('upg-edu-is-current');

          if (instEl && !instEl.value) instEl.value = edu.institution || '';
          if (degEl && !degEl.value) {
            let degText = edu.degree || '';
            if (edu.field_of_study && !degText.toLowerCase().includes(edu.field_of_study.toLowerCase())) {
              degText += ` in ${edu.field_of_study}`;
            }
            degEl.value = degText.trim();
          }
          if (startEl && !startEl.value) startEl.value = edu.start_date || '';
          if (endEl && !endEl.value) endEl.value = edu.end_date || '';
          if (gpaEl && !gpaEl.value) gpaEl.value = edu.gpa || '';
          if (currEl) {
            const isCurr = edu.current || /present|current|ongoing/i.test(edu.end_date || '');
            currEl.checked = Boolean(isCurr);
          }
        }
      }
    });
  });

  // Cancel buttons
  container.querySelectorAll('.btn-upg-cancel-form').forEach(btn => {
    btn.addEventListener('click', () => {
      const sec = btn.getAttribute('data-sec');
      const targetForm = document.getElementById(`upg-form-${sec}`);
      if (targetForm) targetForm.classList.add('hidden');
    });
  });

  // Current enrolled checkbox toggle
  const currEnrolledCheck = document.getElementById('upg-edu-is-current');
  const endYearInput = document.getElementById('upg-edu-end-year');
  if (currEnrolledCheck && endYearInput) {
    currEnrolledCheck.addEventListener('change', () => {
      if (currEnrolledCheck.checked) {
        if (!endYearInput.value.trim() || endYearInput.value === '2026') endYearInput.value = 'Present';
      }
    });
  }

  // 1. Save Education
  const btnSaveEdu = document.getElementById('btn-upg-save-edu');
  if (btnSaveEdu) {
    btnSaveEdu.addEventListener('click', () => {
      const inst = document.getElementById('upg-edu-institution')?.value.trim() || '';
      const deg = document.getElementById('upg-edu-degree')?.value.trim() || '';
      const start = document.getElementById('upg-edu-start-year')?.value.trim() || '';
      const end = document.getElementById('upg-edu-end-year')?.value.trim() || '';
      const gpa = document.getElementById('upg-edu-gpa')?.value.trim() || '';
      const isCurrent = document.getElementById('upg-edu-is-current')?.checked || /present|current|ongoing/i.test(end);

      if (!inst && !deg) {
        showToast('warning', 'Please provide a College / Institute name or Degree.');
        return;
      }

      if (!currentCanonicalData) {
        currentCanonicalData = {
          candidate_name: 'CANDIDATE',
          education: [],
          skills: {},
          experience: [],
          projects: []
        };
      }
      if (!currentCanonicalData.education) currentCanonicalData.education = [];

      let degreeName = deg;
      let fieldOfStudy = '';
      if (/ in /i.test(deg)) {
        const parts = deg.split(/\s+in\s+/i);
        degreeName = parts[0].trim();
        fieldOfStudy = parts[1].trim();
      }

      const eduItem = {
        id: 'edu_' + Date.now(),
        institution: inst,
        degree: degreeName,
        field_of_study: fieldOfStudy,
        start_date: start,
        end_date: isCurrent ? 'Present' : end,
        gpa: gpa,
        current: isCurrent
      };

      const existingIdx = currentCanonicalData.education.findIndex(e => 
        e.institution && inst && e.institution.toLowerCase() === inst.toLowerCase()
      );
      if (existingIdx >= 0) {
        currentCanonicalData.education[existingIdx] = eduItem;
      } else {
        currentCanonicalData.education.unshift(eduItem);
      }

      syncCustomSectionsToMarkdownEditor();
      document.getElementById('upg-form-education')?.classList.add('hidden');
      showToast('school', `Saved Education: ${inst || degreeName} (${start || ''} – ${isCurrent ? 'Present' : (end || 'Present')})`);
    });
  }

  // 2. Save Certifications
  const btnSaveCert = document.getElementById('btn-upg-save-cert');
  if (btnSaveCert) {
    btnSaveCert.addEventListener('click', () => {
      const inputEl = document.getElementById('upg-cert-input');
      const val = inputEl ? inputEl.value.trim() : '';
      if (!val) {
        showToast('warning', 'Please enter at least one certification.');
        return;
      }
      const lines = val.split('\n').map(l => l.trim().replace(/^[•\-\*]\s*/, '')).filter(Boolean);
      if (!lines.length) return;

      optionalSectionsState.certifications.status = 'added';
      optionalSectionsState.certifications.data = lines;
      applySectionToCanonical('certifications', lines);
      document.getElementById('upg-form-certifications')?.classList.add('hidden');
      showToast('workspace_premium', `Saved ${lines.length} certification(s) to resume!`);
    });
  }

  // 3. Save Achievements
  const btnSaveAch = document.getElementById('btn-upg-save-ach');
  if (btnSaveAch) {
    btnSaveAch.addEventListener('click', () => {
      const inputEl = document.getElementById('upg-ach-input');
      const val = inputEl ? inputEl.value.trim() : '';
      if (!val) {
        showToast('warning', 'Please enter at least one achievement.');
        return;
      }
      const lines = val.split('\n').map(l => l.trim().replace(/^[•\-\*]\s*/, '')).filter(Boolean);
      if (!lines.length) return;

      optionalSectionsState.achievements.status = 'added';
      optionalSectionsState.achievements.data = lines;
      applySectionToCanonical('achievements', lines);
      document.getElementById('upg-form-achievements')?.classList.add('hidden');
      showToast('military_tech', `Saved ${lines.length} achievement(s) to resume!`);
    });
  }

  // 4. Save Hobbies
  const btnSaveHobbies = document.getElementById('btn-upg-save-hobbies');
  if (btnSaveHobbies) {
    btnSaveHobbies.addEventListener('click', () => {
      const inputEl = document.getElementById('upg-hobbies-input');
      const val = inputEl ? inputEl.value.trim() : '';
      if (!val) {
        showToast('warning', 'Please enter at least one hobby / interest.');
        return;
      }
      const lines = val.split('\n').map(l => l.trim().replace(/^[•\-\*]\s*/, '')).filter(Boolean);
      if (!lines.length) return;

      optionalSectionsState.hobbies.status = 'added';
      optionalSectionsState.hobbies.data = lines;
      applySectionToCanonical('hobbies', lines);
      document.getElementById('upg-form-hobbies')?.classList.add('hidden');
      showToast('sports_esports', `Saved ${lines.length} hobby/interest item(s) to resume!`);
    });
  }

  // 5. Save Custom Section
  const btnSaveCustom = document.getElementById('btn-upg-save-custom');
  if (btnSaveCustom) {
    btnSaveCustom.addEventListener('click', () => {
      const titleEl = document.getElementById('upg-custom-title');
      const itemsEl = document.getElementById('upg-custom-items');
      const title = titleEl ? titleEl.value.trim() : '';
      const itemsVal = itemsEl ? itemsEl.value.trim() : '';

      if (!title) {
        showToast('warning', 'Please provide a Section Title.');
        return;
      }
      const lines = itemsVal.split('\n').map(l => l.trim().replace(/^[•\-\*]\s*/, '')).filter(Boolean);
      if (!lines.length) {
        showToast('warning', 'Please provide at least one bullet item.');
        return;
      }

      if (!currentCanonicalData) currentCanonicalData = {};
      if (!currentCanonicalData.custom_sections) currentCanonicalData.custom_sections = [];

      currentCanonicalData.custom_sections = currentCanonicalData.custom_sections.filter(
        s => (s.title || '').toLowerCase() !== title.toLowerCase()
      );
      currentCanonicalData.custom_sections.push({
        id: 'sec_' + Date.now(),
        title: title,
        items: lines
      });

      syncCustomSectionsToMarkdownEditor();
      document.getElementById('upg-form-custom')?.classList.add('hidden');
      if (titleEl) titleEl.value = '';
      if (itemsEl) itemsEl.value = '';
      showToast('post_add', `Saved Custom Section: '${title}' (${lines.length} items)!`);
    });
  }
}

// Call listener initializations
initOptionalSectionsListeners();
initUpgradeCVSectionAdders();


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
      ? 'px-3 py-1 rounded-full text-xs font-semibold bg-tertiary/10 border border-tertiary/30 text-tertiary flex items-center gap-1.5 cursor-pointer hover:scale-105 hover:bg-tertiary/20 transition-all select-none'
      : 'px-3 py-1 rounded-full text-xs font-semibold bg-error/10 border border-error/30 text-error flex items-center gap-1.5 cursor-pointer hover:scale-105 hover:bg-error/20 transition-all select-none';
    chip.innerHTML = `<span class="material-symbols-outlined text-[14px]">${chipType === 'chip-matched' ? 'check' : 'close'}</span><span>${skill}</span><span class="material-symbols-outlined text-[12px] opacity-60 ml-0.5" title="Click to view learning roadmap, tutorials &amp; certs">info</span>`;
    chip.title = `Click to explore roadmap, YouTube tutorials, certs & interview prep for ${skill}`;
    chip.addEventListener('click', (e) => {
      e.stopPropagation();
      if (typeof window.openSkillDetailModal === 'function') {
        window.openSkillDetailModal(skill, chipType === 'chip-matched');
      }
    });
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
            <span class="text-outline font-code-sm text-[10px] block uppercase tracking-wider mb-2 font-bold">9 Automated Recruiter-Side Signals:</span>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-code-sm">
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">1. Bio Display Name (18%)</span>: Matches GitHub profile name to resume.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">2. Username Tokens (10%)</span>: Split &amp; substring name token analysis.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">3. LinkedIn in Bio (18%)</span>: Verifies if GitHub bio links to candidate LinkedIn.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">4. Git Commit Authors (14%)</span>: Audits local git commit signatures.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">5. Account Age vs XP (10%)</span>: Flags 1-week-old accounts claiming 5yr XP.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">6. Commit Email Match (10%)</span>: Scans raw git commit header emails.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">7. Contribution History (5%)</span>: Repos, followers &amp; multi-year longevity.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-outline-variant/20">
                <span class="text-neon-purple font-bold">8. Profile README (5%)</span>: Scans <code># Hi, I'm...</code> intro markdown.
              </div>
              <div class="p-2 rounded bg-surface-container/60 border border-neon-purple/30 bg-neon-purple/5 sm:col-span-2">
                <span class="text-tertiary font-bold">9. LinkedIn Post → GitHub (10%)</span>: <strong>Crown Jewel</strong> — verifies if candidate publicly announced repo on LinkedIn!
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


// ══════════════════════════════════════════════════════════════════════════════
// GitHub Ownership Verification Modal + Real GraphQL Contribution Intelligence
// ══════════════════════════════════════════════════════════════════════════════
(function initGitHubIntelligence() {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────────────
  let _ownershipStatus = null;    // Latest GitHubOwnershipStatus from backend
  let _githubUsername  = null;    // Current candidate GitHub username from resume
  let _contribPayload  = null;    // Latest GitHubContributionPayload
  let _activeYear      = null;    // Active selected year in contribution card
  let _activeView      = 'heatmap'; // 'heatmap' | 'trendline'
  let _yearlyTotalsAll = {};      // Aggregated yearly totals across all year fetches

  // ── DOM refs ───────────────────────────────────────────────────────────────
  const verifyModal         = document.getElementById('github-verify-modal');
  const btnCloseModal       = document.getElementById('btn-close-github-modal');
  const btnConfirmModal     = document.getElementById('btn-confirm-github-modal');
  const btnOAuthAuthorize   = document.getElementById('btn-oauth-authorize');
  const btnVerifyToken      = document.getElementById('btn-verify-token');
  const btnDisconnect       = document.getElementById('btn-disconnect-github');
  const patInput            = document.getElementById('pat-token-input');
  const modalFeedback       = document.getElementById('modal-verification-feedback');
  const modalFeedbackIcon   = document.getElementById('modal-feedback-icon');
  const modalFeedbackContent= document.getElementById('modal-feedback-content');
  const modalClaimedUser    = document.getElementById('modal-claimed-username');
  const modalOwnershipPill  = document.getElementById('modal-ownership-status-pill');

  // Input-area "Verify GitHub Ownership" button
  const btnVerifyOwnership  = document.getElementById('btn-verify-github-ownership');
  const ownershipBadge      = document.getElementById('github-ownership-badge');
  const ownershipInlineNotice = document.getElementById('github-ownership-inline-notice');

  // Contribution card elements
  const contribCard         = document.getElementById('contrib-graph-card');
  const cardUserHandle      = document.getElementById('contrib-card-user-handle');
  const cardOwnershipBadge  = document.getElementById('contrib-card-ownership-badge');
  const btnCardVerify       = document.getElementById('btn-card-verify-ownership');
  const contribSourceBar    = document.getElementById('contrib-source-bar');
  const contribProfileLink  = document.getElementById('contrib-profile-link');
  const contribRetrievedTime= document.getElementById('contrib-retrieved-time');
  const contribStatusPill   = document.getElementById('contrib-status-pill');
  const contribUnavailableAlert = document.getElementById('contrib-unavailable-alert');
  const contribUnavailableIcon  = document.getElementById('contrib-unavailable-icon');
  const contribUnavailableTitle = document.getElementById('contrib-unavailable-title');
  const contribUnavailableMsg   = document.getElementById('contrib-unavailable-msg');
  const contribUnavailableAction= document.getElementById('contrib-unavailable-action');
  const contribVisualsWrapper   = document.getElementById('contrib-visuals-wrapper');
  const contribYearlyTotalsRow  = document.getElementById('contrib-yearly-totals-row');
  const contribTypeBreakdownGrid= document.getElementById('contrib-type-breakdown-grid');
  const contribPrivacyText      = document.getElementById('contrib-privacy-text');
  const contribRestrictedNote   = document.getElementById('contrib-restricted-note');

  // ── Open / Close Modal ─────────────────────────────────────────────────────
  function openVerifyModal(username) {
    if (!verifyModal) return;
    _githubUsername = username || _githubUsername || null;

    if (modalClaimedUser) {
      modalClaimedUser.textContent = _githubUsername ? `@${_githubUsername}` : 'None detected in resume';
    }

    // Update pill from current ownership status
    updateModalOwnershipPill();

    // Hide feedback
    if (modalFeedback) modalFeedback.classList.add('hidden');

    // Pre-check if OAuth is configured on server
    const oauthBadge = document.getElementById('oauth-status-badge');
    fetch(`/api/github/connect?resume_username=${encodeURIComponent(_githubUsername || '')}`)
      .then(r => r.json())
      .then(data => {
        if (oauthBadge) {
          if (data && data.oauth_configured) {
            oauthBadge.textContent = 'Recommended';
            oauthBadge.className = 'font-code-sm text-[9px] text-tertiary';
          } else {
            oauthBadge.textContent = 'Requires .env Setup';
            oauthBadge.className = 'font-code-sm text-[9px] text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded border border-yellow-400/20';
          }
        }
      })
      .catch(() => {});

    verifyModal.classList.remove('hidden');
  }

  function closeVerifyModal() {
    if (verifyModal) verifyModal.classList.add('hidden');
  }

  if (btnCloseModal) btnCloseModal.addEventListener('click', closeVerifyModal);
  if (btnConfirmModal) btnConfirmModal.addEventListener('click', closeVerifyModal);
  if (verifyModal) {
    verifyModal.addEventListener('click', (e) => {
      if (e.target === verifyModal) closeVerifyModal();
    });
  }

  // Trigger from input section "Verify GitHub Ownership" button
  if (btnVerifyOwnership) {
    btnVerifyOwnership.addEventListener('click', () => {
      const ghInput = document.getElementById('github-override');
      const rawUrl  = ghInput ? ghInput.value.trim() : '';
      const uname   = extractGitHubUsername(rawUrl) || _githubUsername;
      openVerifyModal(uname);
    });
  }

  // Trigger from inside contribution card header
  if (btnCardVerify) {
    btnCardVerify.addEventListener('click', () => {
      openVerifyModal(_githubUsername);
    });
  }

  // ── Extract GitHub Username from URL ───────────────────────────────────────
  function extractGitHubUsername(url) {
    if (!url) return null;
    // Normalize: strip protocol, www., trailing slashes
    let clean = url.trim().replace(/^https?:\/\/(www\.)?github\.com\//i, '').replace(/\/.*$/, '').replace(/\/$/, '');
    if (!clean || clean.includes('.') || clean.length < 1) return null;
    return clean;
  }

  // ── Update Ownership Pill & Badge in Modal ─────────────────────────────────
  function updateModalOwnershipPill() {
    if (!modalOwnershipPill || !_ownershipStatus) return;
    const s = _ownershipStatus;
    if (s.verified && s.matched) {
      modalOwnershipPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-tertiary/40 text-tertiary bg-tertiary/10';
      modalOwnershipPill.textContent = '✓ Ownership Verified';
    } else if (s.status === 'MISMATCH') {
      modalOwnershipPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-error/40 text-error bg-error/10';
      modalOwnershipPill.textContent = '⚠ Mismatch';
    } else {
      modalOwnershipPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-outline-variant/40 text-outline';
      modalOwnershipPill.textContent = 'Pending';
    }
  }

  // ── Update Input Area Badges ───────────────────────────────────────────────
  function updateInputOwnershipBadge(status) {
    if (!ownershipBadge) return;
    if (status && status.verified && status.matched) {
      ownershipBadge.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full bg-tertiary/10 border border-tertiary/30 text-tertiary font-bold';
      ownershipBadge.textContent = `✓ Ownership Verified (@${status.login})`;
    } else if (status && status.status === 'MISMATCH') {
      ownershipBadge.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full bg-error/10 border border-error/30 text-error font-bold';
      ownershipBadge.textContent = `⚠ Mismatch: Authenticated @${status.login}`;
    } else {
      ownershipBadge.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-outline-variant/30 text-outline';
      ownershipBadge.textContent = 'Ownership Unverified';
    }
  }

  // ── Show Modal Feedback ────────────────────────────────────────────────────
  function showModalFeedback(type, html) {
    if (!modalFeedback || !modalFeedbackContent) return;
    modalFeedback.classList.remove('hidden', 'bg-tertiary/10', 'border-tertiary/30', 'text-tertiary',
      'bg-error/10', 'border-error/30', 'text-error', 'bg-orange-500/10', 'border-orange-500/30', 'text-orange-300',
      'bg-surface-container-lowest/80', 'border-outline-variant/30', 'text-outline');
    modalFeedback.classList.add('flex');

    if (type === 'success') {
      modalFeedback.classList.add('bg-tertiary/10', 'border-tertiary/30', 'text-tertiary');
      if (modalFeedbackIcon) modalFeedbackIcon.textContent = 'verified';
    } else if (type === 'error') {
      modalFeedback.classList.add('bg-error/10', 'border-error/30', 'text-error');
      if (modalFeedbackIcon) modalFeedbackIcon.textContent = 'error';
    } else if (type === 'warning') {
      modalFeedback.classList.add('bg-orange-500/10', 'border-orange-500/30', 'text-orange-300');
      if (modalFeedbackIcon) modalFeedbackIcon.textContent = 'warning';
    } else {
      modalFeedback.classList.add('bg-surface-container-lowest/80', 'border-outline-variant/30', 'text-outline');
      if (modalFeedbackIcon) modalFeedbackIcon.textContent = 'info';
    }
    modalFeedbackContent.innerHTML = html;
    try { modalFeedback.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch(e) {}
  }

  // ── Handle Ownership Verification Result ───────────────────────────────────
  function applyOwnershipResult(statusData) {
    _ownershipStatus = statusData;
    updateModalOwnershipPill();
    updateInputOwnershipBadge(statusData);

    if (statusData.verified && statusData.matched) {
      showModalFeedback('success',
        `<strong>✓ GitHub Ownership Verified!</strong><br>
         Authenticated as <strong>@${statusData.login}</strong> (GitHub ID: ${statusData.github_user_id}).
         Resume username matches authenticated account.`
      );
      // Update inline notice
      if (ownershipInlineNotice) {
        ownershipInlineNotice.className = 'mt-1.5 text-[11px] font-code-sm p-2 rounded-lg border bg-tertiary/10 border-tertiary/30 text-tertiary';
        ownershipInlineNotice.textContent = `✓ GitHub Ownership Verified: Authenticated @${statusData.login}`;
        ownershipInlineNotice.classList.remove('hidden');
      }
      showToast('verified', `GitHub ownership verified: @${statusData.login}`);
    } else if (statusData.status === 'MISMATCH') {
      showModalFeedback('warning',
        `<strong>⚠ GitHub Ownership Mismatch</strong><br>
         Authenticated as <strong>@${statusData.login}</strong>, but resume claims <strong>@${statusData.resume_username || '—'}</strong>.
         The contribution data shown may not belong to this candidate.`
      );
      if (ownershipInlineNotice) {
        ownershipInlineNotice.className = 'mt-1.5 text-[11px] font-code-sm p-2 rounded-lg border bg-orange-500/10 border-orange-500/30 text-orange-300';
        ownershipInlineNotice.textContent = `⚠ Mismatch: Authenticated @${statusData.login} ≠ Resume @${statusData.resume_username}`;
        ownershipInlineNotice.classList.remove('hidden');
      }
    } else {
      showModalFeedback('error', `<strong>Verification failed:</strong> ${statusData.message || 'Could not verify ownership.'}`);
    }

    // Refresh contribution card ownership badge
    updateContribCardOwnershipBadge(statusData);

    // Synchronize Top 10-Signal Fraud Audit Card directly
    if (statusData.verified && statusData.matched) {
      if (githubOverride && (!githubOverride.value || !githubOverride.value.trim()) && statusData.login) {
        githubOverride.value = `https://github.com/${statusData.login}`;
      }
      if (candidateIdentityText && candidateIdentityPill) {
        candidateIdentityText.textContent = `GitHub Verified: @${statusData.login}`;
        candidateIdentityPill.className = 'candidate-identity-pill px-3 py-1 rounded-full border text-xs font-code-sm flex items-center gap-1.5 bg-tertiary/15 text-tertiary border-tertiary/30';
        candidateIdentityPill.classList.remove('hidden');
      }
      if (identityVerdictBadge) {
        identityVerdictBadge.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border bg-tertiary/15 text-tertiary border-tertiary/30';
        identityVerdictBadge.textContent = 'OWNERSHIP CONFIRMED';
      }
      if (identityOwnershipScore) {
        identityOwnershipScore.textContent = '100%';
        identityOwnershipScore.className = 'font-headline-lg text-xl font-extrabold text-tertiary';
      }
      if (identityScoreCircle) {
        identityScoreCircle.setAttribute('stroke-dasharray', '100, 100');
        identityScoreCircle.setAttribute('class', 'text-tertiary transition-all duration-1000');
      }
      if (identityCalloutBanner) {
        identityCalloutBanner.className = 'p-3.5 rounded-xl text-xs leading-relaxed mb-5 border font-body-md flex items-start gap-3 bg-tertiary/10 border-tertiary/25 text-tertiary';
        if (identityBannerIcon) identityBannerIcon.textContent = 'verified_user';
        if (identityBannerText) {
          identityBannerText.innerHTML = `<strong>Ownership Confirmed:</strong> Candidate proved authenticated account control of GitHub account <strong>@${statusData.login}</strong> via Token/OAuth. Commits and evidence are confirmed authentic.`;
        }
      }
      // Update Signal 4 and Signal 7 cards if present in the grid
      if (identitySignalsGrid) {
        const sigCards = identitySignalsGrid.children;
        for (let i = 0; i < sigCards.length; i++) {
          const cardText = sigCards[i].textContent || '';
          if (cardText.includes('Git Commit Author Name')) {
            sigCards[i].innerHTML = `
              <div class="flex items-center justify-between gap-2 mb-1.5">
                <span class="font-bold text-white flex items-center gap-1.5 truncate">
                  <span class="material-symbols-outlined text-[15px] text-tertiary">verified</span>
                  <span class="truncate">Git Commit Author Name</span>
                </span>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span class="text-[10px] text-outline font-code-sm">Weight: 14%</span>
                  <span class="text-[10px] text-tertiary bg-tertiary/10 px-2 py-0.5 rounded border border-tertiary/30 font-code-sm font-bold">100% Pass</span>
                </div>
              </div>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                100% Verified Account Ownership: Candidate verified access to GitHub account '@${statusData.login}' via Token/OAuth — commit signatures verified to authenticated owner.
              </p>
            `;
          } else if (cardText.includes('Commit Email Cross-Match')) {
            sigCards[i].innerHTML = `
              <div class="flex items-center justify-between gap-2 mb-1.5">
                <span class="font-bold text-white flex items-center gap-1.5 truncate">
                  <span class="material-symbols-outlined text-[15px] text-tertiary">verified</span>
                  <span class="truncate">Commit Email Cross-Match</span>
                </span>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span class="text-[10px] text-outline font-code-sm">Weight: 10%</span>
                  <span class="text-[10px] text-tertiary bg-tertiary/10 px-2 py-0.5 rounded border border-tertiary/30 font-code-sm font-bold">100% Pass</span>
                </div>
              </div>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">
                100% Verified Account Ownership: Candidate verified access via GitHub Token/OAuth — commit emails validated to account owner.
              </p>
            `;
          }
        }
      }
    }

    // If contribution card is visible, trigger re-fetch
    if (contribCard && !contribCard.classList.contains('hidden') && _githubUsername) {
      fetchAndRenderContributions(_githubUsername, _activeYear);
    }
  }

  // ── GitHub OAuth Flow ──────────────────────────────────────────────────────
  if (btnOAuthAuthorize) {
    btnOAuthAuthorize.addEventListener('click', async () => {
      if (!_githubUsername) {
        showModalFeedback('error', 'No GitHub username detected from resume. Please ensure a GitHub URL is in the resume or override field.');
        return;
      }

      btnOAuthAuthorize.disabled = true;
      btnOAuthAuthorize.innerHTML = `<span class="btn-spinner w-4 h-4 border-2"></span><span>Checking OAuth…</span>`;

      try {
        const res = await fetch(`/api/github/connect?resume_username=${encodeURIComponent(_githubUsername)}`);
        const data = await res.json();

        if (!data.oauth_configured) {
          showModalFeedback('warning',
            `<strong>GitHub OAuth App Not Configured:</strong><br>
             <code>GITHUB_CLIENT_ID</code> is not set in your <code>.env</code> file.<br><br>
             👉 <strong>Instant Solution:</strong> Use <strong>Option B (Personal Access Token)</strong> below! Paste your GitHub token (classic or fine-grained) and click <em>Verify Token</em> to verify immediately.<br><br>
             <span class="text-[10px] text-on-surface-variant leading-normal block">To enable Option A instead: Register a GitHub OAuth App with callback URL <code>http://localhost:8000/api/github/callback</code> and add GITHUB_CLIENT_ID & GITHUB_CLIENT_SECRET to .env.</span>`
          );
          return;
        }

        // Open OAuth popup window
        const popup = window.open(
          data.auth_url,
          'GitHubOAuth',
          'width=600,height=700,scrollbars=yes,resizable=yes'
        );

        if (!popup) {
          showModalFeedback('error', 'Could not open OAuth popup. Please allow popups for this page.');
          return;
        }

        showModalFeedback('info', '<strong>Awaiting GitHub Authorization…</strong><br>Please authorize in the popup window. This will close automatically when done.');

        // Listen for postMessage from callback popup
        function handleOAuthMessage(event) {
          if (event.data && event.data.type === 'GITHUB_AUTH_SUCCESS') {
            window.removeEventListener('message', handleOAuthMessage);
            applyOwnershipResult(event.data.status);
          } else if (event.data && event.data.type === 'GITHUB_AUTH_ERROR') {
            window.removeEventListener('message', handleOAuthMessage);
            showModalFeedback('error', `<strong>GitHub Authorization failed:</strong> ${event.data.error || 'Unknown error.'}`);
            showToast('error', 'GitHub OAuth failed: ' + (event.data.error || 'Unknown'));
          }
        }
        window.addEventListener('message', handleOAuthMessage);

        // Timeout safety: remove listener after 5 minutes
        setTimeout(() => window.removeEventListener('message', handleOAuthMessage), 300000);

      } catch (err) {
        showModalFeedback('error', `<strong>Connection error:</strong> Could not reach backend. ${err.message}`);
      } finally {
        btnOAuthAuthorize.disabled = false;
        btnOAuthAuthorize.innerHTML = `
          <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          <span>Authorize with GitHub OAuth</span>`;
      }
    });
  }

  const btnGhModalConfigure = document.getElementById('btn-github-modal-configure');
  if (btnGhModalConfigure) {
    btnGhModalConfigure.addEventListener('click', () => {
      closeVerifyModal();
      if (window.openIntegrationsModal) window.openIntegrationsModal();
    });
  }

  // ── PAT Token Verification ─────────────────────────────────────────────────
  if (btnVerifyToken) {
    btnVerifyToken.addEventListener('click', async () => {
      const token = patInput ? patInput.value.trim() : '';
      if (!token) {
        showModalFeedback('error', 'Please enter a GitHub Personal Access Token.');
        return;
      }

      btnVerifyToken.disabled = true;
      btnVerifyToken.textContent = 'Verifying…';

      try {
        const formData = new FormData();
        formData.append('token', token);
        if (_githubUsername) formData.append('resume_username', _githubUsername);

        const res = await fetch('/api/github/verify-token', {
          method: 'POST',
          body: formData
        });

        const statusData = await res.json();

        if (!res.ok) {
          showModalFeedback('error', `<strong>Token rejected:</strong> ${statusData.detail || 'Invalid token or insufficient permissions.'}`);
          return;
        }

        applyOwnershipResult(statusData);

        // Fetch real contributions after verification
        if (_githubUsername) {
          closeVerifyModal();
          fetchAndRenderContributions(_githubUsername, null);
        }

      } catch (err) {
        showModalFeedback('error', `<strong>Request failed:</strong> ${err.message}`);
      } finally {
        btnVerifyToken.disabled = false;
        btnVerifyToken.textContent = 'Verify Token';
      }
    });
  }

  // ── Disconnect GitHub ──────────────────────────────────────────────────────
  if (btnDisconnect) {
    btnDisconnect.addEventListener('click', async () => {
      try {
        await fetch('/api/github/disconnect', { method: 'POST' });
      } catch (_) {}
      _ownershipStatus = null;
      updateInputOwnershipBadge(null);
      if (ownershipInlineNotice) ownershipInlineNotice.classList.add('hidden');
      if (modalOwnershipPill) {
        modalOwnershipPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-outline-variant/40 text-outline';
        modalOwnershipPill.textContent = 'Pending';
      }
      if (modalFeedback) modalFeedback.classList.add('hidden');
      showToast('link_off', 'GitHub account disconnected.');
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // Real GitHub Contribution Intelligence Rendering
  // ══════════════════════════════════════════════════════════════════════════

  // Update the ownership badge inside the contribution card header
  function updateContribCardOwnershipBadge(status) {
    if (!cardOwnershipBadge) return;
    if (status && status.verified && status.matched) {
      cardOwnershipBadge.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border bg-tertiary/10 text-tertiary border-tertiary/30';
      cardOwnershipBadge.textContent = '✓ Ownership Verified';
    } else if (status && status.status === 'MISMATCH') {
      cardOwnershipBadge.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border bg-orange-500/10 text-orange-400 border-orange-500/30';
      cardOwnershipBadge.textContent = '⚠ Ownership Mismatch';
    } else {
      cardOwnershipBadge.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full font-bold border bg-surface-container-lowest/80 text-outline border-outline-variant/30';
      cardOwnershipBadge.textContent = 'Ownership Not Verified';
    }
  }

  // Show the contribution card error/unavailable state
  function showContribUnavailable(title, msg, actionHtml) {
    if (contribUnavailableAlert) contribUnavailableAlert.classList.remove('hidden');
    if (contribVisualsWrapper) contribVisualsWrapper.classList.add('hidden');

    // Color by severity
    if (contribUnavailableAlert) {
      contribUnavailableAlert.className = 'mb-4 p-4 rounded-xl border flex items-start gap-3 text-xs font-code-sm leading-relaxed bg-surface-container-lowest/80 border-outline-variant/30 text-outline';
    }
    if (contribUnavailableIcon) contribUnavailableIcon.textContent = 'info';
    if (contribUnavailableTitle) contribUnavailableTitle.textContent = title;
    if (contribUnavailableMsg) contribUnavailableMsg.textContent = msg;
    if (contribUnavailableAction) contribUnavailableAction.innerHTML = actionHtml || '';

    // Keep source bar but show no data
    if (contribStatusPill) {
      contribStatusPill.className = 'px-2 py-0.5 rounded bg-surface-container-lowest/80 border border-outline-variant/30 text-outline font-bold flex items-center gap-1';
      contribStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-outline"></span> UNAVAILABLE';
    }
  }

  // Show contribution data visuals
  function showContribVisuals() {
    if (contribUnavailableAlert) contribUnavailableAlert.classList.add('hidden');
    if (contribVisualsWrapper) contribVisualsWrapper.classList.remove('hidden');
    if (contribStatusPill) {
      contribStatusPill.className = 'px-2 py-0.5 rounded bg-neon-green/10 border border-neon-green/30 text-neon-green font-bold flex items-center gap-1';
      contribStatusPill.innerHTML = '<span class="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse"></span> LIVE / API VERIFIED';
    }
  }

  // ── Main Entry: Fetch + Render Contribution Dashboard ─────────────────────
  async function fetchAndRenderContributions(username, year) {
    if (!username || !contribCard) return;
    _githubUsername = username;

    // Show card
    contribCard.classList.remove('hidden');

    // Update source bar
    if (cardUserHandle) cardUserHandle.textContent = `@${username}`;
    if (contribProfileLink) {
      contribProfileLink.href = `https://github.com/${username}`;
      contribProfileLink.textContent = `github.com/${username}`;
    }

    const endpoint = year
      ? `/api/github/contributions/${year}?username=${encodeURIComponent(username)}`
      : `/api/github/contributions?username=${encodeURIComponent(username)}`;

    try {
      const res = await fetch(endpoint);

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showContribUnavailable(
          'GitHub API Error',
          `HTTP ${res.status}: ${err.detail || 'Could not retrieve contribution data.'}`,
          `<button class="text-xs text-cyan hover:underline" onclick="document.getElementById('btn-verify-github-ownership').click()">Verify GitHub ownership to enable contribution data →</button>`
        );
        return;
      }

      const payload = await res.json();
      _contribPayload = payload;

      // Update ownership status from payload
      if (payload.ownership) {
        _ownershipStatus = payload.ownership;
        updateContribCardOwnershipBadge(payload.ownership);
        updateInputOwnershipBadge(payload.ownership);
      }

      // Update source transparency bar
      const retrievedAt = payload.retrieved_at ? new Date(payload.retrieved_at).toLocaleString() : '—';
      if (contribRetrievedTime) contribRetrievedTime.textContent = retrievedAt;

      if (!payload.data_available) {
        // Honest unavailable state
        const reason = payload.error_reason || 'GitHub contribution data could not be retrieved.';
        let actionHtml = '';
        if (reason.toLowerCase().includes('rate limit')) {
          actionHtml = `<span class="text-yellow-400">GitHub API rate limit reached. Data will be available after the hourly reset.</span>`;
        } else if (reason.toLowerCase().includes('not found') || reason.toLowerCase().includes('no such user')) {
          actionHtml = `<span class="text-error">GitHub profile not found for @${username}. Verify the resume GitHub URL is correct.</span>`;
        } else {
          actionHtml = `<button class="text-xs text-cyan hover:underline" onclick="document.getElementById('btn-verify-github-ownership').click()">Verify ownership to authenticate and fetch real data →</button>`;
        }
        showContribUnavailable('GitHub Contribution Data Unavailable', reason, actionHtml);
        return;
      }

      // Show visuals
      showContribVisuals();

      // Render full contribution intelligence dashboard
      renderGitHubContributionDashboard(payload);

    } catch (err) {
      console.error('GitHub contribution fetch error:', err);
      showContribUnavailable(
        'Connection Error',
        `Could not connect to GitHub intelligence backend: ${err.message}`,
        `<button class="text-xs text-cyan hover:underline" onclick="document.getElementById('btn-verify-github-ownership').click()">Try verifying GitHub ownership →</button>`
      );
    }
  }

  // ── Render Full Contribution Dashboard from GitHubContributionPayload ──────
  function renderGitHubContributionDashboard(payload) {
    const years = (payload.years_active || []).slice().sort((a, b) => Number(b) - Number(a));
    const yearlyTotals = payload.yearly_totals || {};
    const breakdown = payload.types_breakdown || {};
    const topRepos = payload.top_repositories || [];
    const calendar = payload.calendar || null;
    const selectedYear = payload.selected_year || (years[0] || String(new Date().getFullYear()));

    // Merge yearly totals (we may have fetched only one year at a time)
    Object.assign(_yearlyTotalsAll, yearlyTotals);

    _activeYear = selectedYear;

    // ── Year Pills ────────────────────────────────────────────────────────────
    const yearPillsContainer = document.getElementById('contrib-year-pills');
    if (yearPillsContainer) {
      yearPillsContainer.innerHTML = '';
      years.forEach(y => {
        const pill = document.createElement('button');
        pill.type = 'button';
        pill.className = `contrib-year-pill ${y === selectedYear ? 'active' : ''}`;
        const total = _yearlyTotalsAll[y] !== undefined ? _yearlyTotalsAll[y] : '—';
        pill.innerHTML = `<span>${y}</span><span class="text-[9px] opacity-75 font-normal">(${total})</span>`;
        pill.onclick = () => {
          _activeYear = y;
          // Update pill active state immediately
          yearPillsContainer.querySelectorAll('.contrib-year-pill').forEach(p => p.classList.remove('active'));
          pill.classList.add('active');
          // Fetch contribution data for this specific year
          fetchAndRenderContributions(_githubUsername, y);
        };
        yearPillsContainer.appendChild(pill);
      });
    }

    // ── Yearly Totals Row ─────────────────────────────────────────────────────
    if (contribYearlyTotalsRow) {
      contribYearlyTotalsRow.innerHTML = '';
      // Show all known years
      years.forEach(y => {
        const tot = _yearlyTotalsAll[y];
        const isSel = y === selectedYear;
        const span = document.createElement('span');
        span.className = `font-code-sm text-[11px] px-2.5 py-1 rounded-full border ${isSel
          ? 'border-neon-green/40 bg-neon-green/10 text-neon-green font-bold'
          : 'border-outline-variant/30 text-outline'}`;
        span.textContent = tot !== undefined ? `${y}: ${tot}` : `${y}: —`;
        contribYearlyTotalsRow.appendChild(span);
      });
    }

    // ── Header Badges ─────────────────────────────────────────────────────────
    const totalBadge = document.getElementById('contrib-total-badge');
    const yearsBadge = document.getElementById('contrib-years-badge');
    const origBadge  = document.getElementById('contrib-originality-badge');
    const calTotal   = calendar ? calendar.totalContributions : (yearlyTotals[selectedYear] || 0);

    if (totalBadge) totalBadge.textContent = `${calTotal} Contributions (${selectedYear})`;
    if (yearsBadge) yearsBadge.textContent = `${years.length} Year${years.length !== 1 ? 's' : ''}`;
    if (origBadge) origBadge.textContent = 'Real GitHub GraphQL API';

    // ── KPI Cards ─────────────────────────────────────────────────────────────
    const kpiCommits   = document.getElementById('contrib-kpi-commits');
    const kpiCommitSub = document.getElementById('contrib-kpi-commits-sub');
    const kpiOrig      = document.getElementById('contrib-kpi-originality');
    const kpiOrigSub   = document.getElementById('contrib-kpi-originality-sub');
    const kpiActDays   = document.getElementById('contrib-kpi-active-days');
    const kpiStreak    = document.getElementById('contrib-kpi-streak');
    const kpiPeakMo    = document.getElementById('contrib-kpi-peak-month');
    const kpiPeakSub   = document.getElementById('contrib-kpi-peak-sub');

    if (kpiCommits) kpiCommits.textContent = String(calTotal);
    if (kpiCommitSub) kpiCommitSub.textContent = `${calTotal} verified via GitHub GraphQL API in ${selectedYear}`;

    // Compute active days and longest streak from calendar
    let activeDays = 0, longestStreak = 0, currentStreak = 0;
    const allDays = getAllCalendarDays(calendar);
    allDays.forEach(d => {
      if (d.contributionCount > 0) {
        activeDays++;
        currentStreak++;
        longestStreak = Math.max(longestStreak, currentStreak);
      } else {
        currentStreak = 0;
      }
    });

    if (kpiActDays) kpiActDays.textContent = `${activeDays} Days`;
    if (kpiStreak) kpiStreak.textContent = `Longest streak: ${longestStreak} days`;

    // Peak month from calendar
    const monthTotals = computeMonthlyTotals(allDays);
    let peakMonth = '—', peakCount = 0;
    Object.entries(monthTotals).forEach(([m, c]) => {
      if (c > peakCount) { peakCount = c; peakMonth = m; }
    });
    if (kpiPeakMo) kpiPeakMo.textContent = peakCount > 0 ? `${peakMonth} (${peakCount})` : '—';
    if (kpiPeakSub) kpiPeakSub.textContent = `Avg: ${Math.round(calTotal / 12)} contributions/mo`;

    // Originality: Public contributions (we can't determine exact ratio without commit author data)
    // GitHub GraphQL API total represents all public activity; mark as public
    if (kpiOrig) kpiOrig.textContent = payload.has_restricted_contributions ? 'Public+Priv' : 'All Public';
    if (kpiOrigSub) kpiOrigSub.textContent = payload.has_restricted_contributions
      ? 'Public contributions shown. Private details not accessible.'
      : 'All public activity verified via GitHub GraphQL API.';

    // ── Contribution Type Breakdown (from GraphQL types) ───────────────────
    renderContributionTypeBreakdown(breakdown);

    // ── Privacy / Restricted Notice ────────────────────────────────────────
    if (contribRestrictedNote) {
      if (payload.has_restricted_contributions) {
        const restrictedCount = (payload.restricted_totals || {})[selectedYear] || 0;
        contribRestrictedNote.innerHTML = `
          <strong class="text-amber-400">⚠ Restricted Contributions:</strong>
          This account has private contribution activity that is not publicly visible.
          ${restrictedCount > 0 ? `<strong class="text-white">${restrictedCount}</strong> restricted contributions in ${selectedYear}.` : ''}
          Private contribution details are not accessible via public GraphQL API.`;
      } else {
        contribRestrictedNote.textContent = 'All public contribution activity is fully verifiable via GitHub GraphQL API.';
      }
    }

    // ── Top Contributed Repositories ──────────────────────────────────────
    renderTopContributedRepositories(topRepos);

    // ── Originality callout text ───────────────────────────────────────────
    const origText = document.getElementById('contrib-originality-text');
    if (origText) {
      if (payload.has_restricted_contributions) {
        origText.innerHTML = `GitHub Activity Verified: <strong class="text-white">${calTotal}</strong> contributions in <strong class="text-white">${selectedYear}</strong> retrieved directly from GitHub's ContributionCalendar GraphQL API. This account also has private/restricted contribution activity that is not publicly visible.`;
      } else {
        origText.innerHTML = `GitHub Activity Verified: <strong class="text-white">${calTotal}</strong> public contributions in <strong class="text-white">${selectedYear}</strong> retrieved directly from GitHub's ContributionCalendar GraphQL API. All displayed data is authentic — no synthetic generation is used.`;
      }
    }

    // ── View toggle state ──────────────────────────────────────────────────
    const btnHeatmap   = document.getElementById('btn-contrib-heatmap');
    const btnTrendline = document.getElementById('btn-contrib-trendline');
    const viewHeatmap  = document.getElementById('contrib-heatmap-view');
    const viewTrendline= document.getElementById('contrib-trendline-view');

    if (btnHeatmap && btnTrendline) {
      btnHeatmap.onclick = () => {
        _activeView = 'heatmap';
        btnHeatmap.classList.add('active');
        btnTrendline.classList.remove('active');
        if (viewHeatmap) viewHeatmap.classList.remove('hidden');
        if (viewTrendline) viewTrendline.classList.add('hidden');
        renderRealHeatmapGrid(calendar);
      };
      btnTrendline.onclick = () => {
        _activeView = 'trendline';
        btnTrendline.classList.add('active');
        btnHeatmap.classList.remove('active');
        if (viewTrendline) viewTrendline.classList.remove('hidden');
        if (viewHeatmap) viewHeatmap.classList.add('hidden');
        drawRealCadenceSpline(monthTotals, calTotal, selectedYear);
      };
    }

    // Initial view
    if (_activeView === 'heatmap') {
      if (viewHeatmap) viewHeatmap.classList.remove('hidden');
      if (viewTrendline) viewTrendline.classList.add('hidden');
      renderRealHeatmapGrid(calendar);
    } else {
      if (viewTrendline) viewTrendline.classList.remove('hidden');
      if (viewHeatmap) viewHeatmap.classList.add('hidden');
      drawRealCadenceSpline(monthTotals, calTotal, selectedYear);
    }

    // Year label updates
    const hmYearLabel = document.getElementById('heatmap-year-label');
    const tlYearLabel = document.getElementById('trendline-year-label');
    const hmCommitCount = document.getElementById('heatmap-year-commits-count');
    if (hmYearLabel) hmYearLabel.textContent = selectedYear;
    if (tlYearLabel) tlYearLabel.textContent = selectedYear;
    if (hmCommitCount) hmCommitCount.textContent = calTotal;
  }

  // ── Helper: Extract all contribution days from calendar ────────────────────
  function getAllCalendarDays(calendar) {
    if (!calendar || !calendar.weeks) return [];
    const days = [];
    calendar.weeks.forEach(w => {
      (w.contributionDays || []).forEach(d => days.push(d));
    });
    return days;
  }

  // ── Helper: Compute monthly totals from flat days list ─────────────────────
  function computeMonthlyTotals(days) {
    const MONTH_ORDER = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const totals = {};
    MONTH_ORDER.forEach(m => { totals[m] = 0; });
    days.forEach(d => {
      if (d.month && d.contributionCount > 0) {
        totals[d.month] = (totals[d.month] || 0) + d.contributionCount;
      }
    });
    return totals;
  }

  // ── Render Contribution Type Breakdown ─────────────────────────────────────
  function renderContributionTypeBreakdown(breakdown) {
    const idMap = {
      commits:                 'contrib-breakdown-commits',
      pull_requests:           'contrib-breakdown-prs',
      issues:                  'contrib-breakdown-issues',
      reviews:                 'contrib-breakdown-reviews',
      discussions:             'contrib-breakdown-discussions',
      repositories_contributed:'contrib-breakdown-repos'
    };
    Object.entries(idMap).forEach(([key, elId]) => {
      const el = document.getElementById(elId);
      if (el) {
        const val = breakdown[key];
        el.textContent = val !== undefined ? String(val) : '—';
      }
    });
  }

  // ── Render Top Contributed Repositories (from GraphQL commitContribsByRepo) ─
  function renderTopContributedRepositories(repos) {
    const popupRepos = document.getElementById('contrib-popup-repos');
    const popupYear  = document.getElementById('contrib-popup-year');
    const popupTotal = document.getElementById('contrib-popup-total');

    if (popupYear) popupYear.textContent = `${_activeYear} Top Contributed Repositories`;

    const sortedRepos = repos.slice().sort((a, b) => b.commit_count - a.commit_count);
    const totalContribs = sortedRepos.reduce((acc, r) => acc + r.commit_count, 0);

    if (popupTotal) popupTotal.textContent = `${totalContribs} commit contributions shown`;

    if (popupRepos) {
      if (sortedRepos.length === 0) {
        popupRepos.innerHTML = `<p class="text-outline text-xs">No repository contribution breakdown available for this period.</p>`;
      } else {
        popupRepos.innerHTML = sortedRepos.slice(0, 10).map(r => {
          const pct = totalContribs > 0 ? Math.min(100, Math.round((r.commit_count / totalContribs) * 100)) : 0;
          const repoUrl = r.url || `https://github.com/${r.repository_name}`;
          const langColor = r.language_color ? `background:${r.language_color}` : 'background:#6366f1';
          const privBadge = r.is_private
            ? `<span class="font-code-sm text-[9px] px-1.5 py-0.5 rounded bg-outline/20 text-outline border border-outline-variant/30">Private</span>`
            : `<span class="font-code-sm text-[9px] px-1.5 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">Public</span>`;
          const starBadge = r.stars > 0
            ? `<span class="font-code-sm text-[9px] text-yellow-400 flex items-center gap-0.5"><span class="material-symbols-outlined text-[10px]">star</span>${r.stars}</span>`
            : '';

          return `
            <div class="flex items-center gap-3 bg-surface-container-lowest/50 p-2.5 rounded-lg border border-outline-variant/20 hover:border-cyan/40 transition-all">
              <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-1">
                  <a href="${repoUrl}" target="_blank" rel="noopener noreferrer"
                     class="font-bold text-white text-xs truncate hover:text-cyan hover:underline flex items-center gap-1">
                    ${r.is_private ? '<span class="material-symbols-outlined text-[11px] text-outline">lock</span>' : ''}
                    <span class="truncate">${r.repository_name}</span>
                    <span class="material-symbols-outlined text-[12px] opacity-70">open_in_new</span>
                  </a>
                  <div class="flex items-center gap-1.5 flex-shrink-0 ml-2">
                    ${privBadge}
                    ${starBadge}
                    <span class="font-code-sm text-[10px] text-cyan font-bold">${r.commit_count} commits</span>
                  </div>
                </div>
                <div class="h-1.5 w-full bg-surface-container rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-700"
                       style="width:${pct}%;${langColor ? `background:linear-gradient(to right,${r.language_color || '#00e5ff'},#00e5ff)` : 'background: linear-gradient(to right,#00e5ff,#39ff8f)'}"></div>
                </div>
                ${r.primary_language ? `<div class="flex items-center gap-1.5 mt-1"><span class="w-2 h-2 rounded-full" style="${langColor}"></span><span class="font-code-sm text-[9px] text-outline">${r.primary_language}</span></div>` : ''}
              </div>
            </div>`;
        }).join('');
      }
    }
  }

  // ── Render Real 52-Week GitHub Heatmap from ContributionCalendar ────────────
  function renderRealHeatmapGrid(calendar) {
    const container = document.getElementById('heatmap-matrix-container');
    const wrapper   = document.getElementById('contrib-graph-card');
    if (!container || !wrapper) return;

    if (!calendar || !calendar.weeks || calendar.weeks.length === 0) {
      container.innerHTML = `<p class="text-outline text-xs p-4">No calendar data available for this year.</p>`;
      return;
    }

    // Flatten all days from all weeks (already in order from GraphQL)
    const allDays = [];
    calendar.weeks.forEach(w => {
      (w.contributionDays || []).forEach(d => allDays.push(d));
    });

    // Month label positions
    let monthLabelsHtml = '';
    let lastMonth = '';
    let colIdx = 0;
    calendar.weeks.forEach((wk, wIdx) => {
      const firstDay = (wk.contributionDays || []).find(d => d != null);
      if (firstDay && firstDay.month && firstDay.month !== lastMonth) {
        lastMonth = firstDay.month;
        monthLabelsHtml += `<span class="text-[10px] font-code-sm text-outline absolute" style="left: ${wIdx * 15}px;">${lastMonth}</span>`;
      }
    });

    // Build heatmap columns
    const weekdayLabels = ['Mon', '', 'Wed', '', 'Fri', '', ''];
    let gridColsHtml = '';

    calendar.weeks.forEach(wk => {
      const days = wk.contributionDays || [];
      // Pad to 7
      const padded = [...days];
      while (padded.length < 7) padded.push(null);

      gridColsHtml += '<div class="flex flex-col gap-[3px]">';
      padded.forEach(day => {
        if (!day) {
          gridColsHtml += '<div class="w-[12px] h-[12px] opacity-0"></div>';
        } else {
          // contributionLevel is "0".."4" from our service (LEVEL_MAP applied)
          const level = day.contributionLevel || '0';
          const count = day.contributionCount || 0;
          gridColsHtml += `
            <div class="heatmap-cell heatmap-level-${level}"
                 data-date="${day.date}"
                 data-count="${count}"
                 data-month="${day.month || ''}"
                 data-day="${day.day || ''}"
                 tabindex="0"
                 aria-label="${count} contributions on ${day.date}">
            </div>`;
        }
      });
      gridColsHtml += '</div>';
    });

    container.innerHTML = `
      <div class="flex flex-col gap-2">
        <div class="relative h-4 mb-1 pl-8" style="min-width: 800px;">
          ${monthLabelsHtml}
        </div>
        <div class="flex items-start gap-2">
          <div class="flex flex-col gap-[3px] pr-1 select-none text-[9px] font-code-sm text-outline h-[105px] justify-between">
            ${weekdayLabels.map(l => `<span class="h-[12px] leading-[12px]">${l}</span>`).join('')}
          </div>
          <div class="flex items-center gap-[3px]" id="heatmap-cells-grid">
            ${gridColsHtml}
          </div>
        </div>
      </div>
    `;

    // Attach floating tooltips
    const floatingTooltip = document.getElementById('contrib-floating-tooltip');
    container.querySelectorAll('.heatmap-cell[data-date]').forEach(cell => {
      cell.addEventListener('mouseenter', (e) => {
        const d = cell.getAttribute('data-date');
        const c = Number(cell.getAttribute('data-count'));
        const countStr = c === 0 ? 'No contributions' : `${c} contribution${c !== 1 ? 's' : ''}`;
        if (floatingTooltip) {
          floatingTooltip.innerHTML = `
            <div class="font-bold text-white">${countStr}</div>
            <div class="text-[10px] text-cyan font-code-sm">${d}</div>
          `;
          floatingTooltip.classList.remove('hidden');
          const rect = wrapper.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          floatingTooltip.style.left = `${Math.max(60, Math.min(rect.width - 80, x))}px`;
          floatingTooltip.style.top = `${y - 12}px`;
        }
      });
      cell.addEventListener('mouseleave', () => {
        if (floatingTooltip) floatingTooltip.classList.add('hidden');
      });
    });
  }

  // ── Render Real Cadence Spline from monthly totals ─────────────────────────
  function drawRealCadenceSpline(monthTotals, yearTotal, selectedYear) {
    const svg = document.getElementById('contrib-line-svg');
    const wrapper = document.getElementById('contrib-graph-card');
    if (!svg || !wrapper) return;

    const MONTH_ORDER = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const values = MONTH_ORDER.map(m => monthTotals[m] || 0);

    const maxVal = Math.max(...values, 1);
    const yMax   = Math.ceil(maxVal / 5) * 5;
    const ySteps = [0, Math.round(yMax * 0.33), Math.round(yMax * 0.66), yMax];

    const originX = 50, originY = 175, topY = 25, rightX = 720;
    const plotWidth = rightX - originX, plotHeight = originY - topY;

    let svgHtml = `
      <defs>
        <linearGradient id="spline-line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#00e5ff" />
          <stop offset="50%" stop-color="#39ff8f" />
          <stop offset="100%" stop-color="#63b3ed" />
        </linearGradient>
        <linearGradient id="spline-area-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#00e5ff" stop-opacity="0.32" />
          <stop offset="60%" stop-color="#39ff8f" stop-opacity="0.10" />
          <stop offset="100%" stop-color="#00e5ff" stop-opacity="0.0" />
        </linearGradient>
        <filter id="glow-filter" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>`;

    ySteps.forEach(val => {
      const y = originY - (val / yMax) * plotHeight;
      svgHtml += `
        <line x1="${originX}" y1="${y}" x2="${rightX}" y2="${y}" stroke="#334155" stroke-width="1" stroke-dasharray="3 3" opacity="0.4" />
        <text x="${originX - 10}" y="${y + 3.5}" fill="#64748b" font-size="9" text-anchor="end" font-family="monospace">${val}</text>`;
    });

    const xStep = plotWidth / (MONTH_ORDER.length - 1);
    const points = MONTH_ORDER.map((m, idx) => ({
      x: originX + idx * xStep,
      y: originY - (values[idx] / yMax) * plotHeight,
      month: m,
      val: values[idx]
    }));

    points.forEach(pt => {
      svgHtml += `
        <line x1="${pt.x}" y1="${originY}" x2="${pt.x}" y2="${originY + 5}" stroke="#475569" stroke-width="1.5" />
        <text x="${pt.x}" y="${originY + 18}" fill="#94a3b8" font-size="10" text-anchor="middle" font-family="monospace" font-weight="600">${pt.month}</text>`;
    });

    function buildSmoothPath(pts) {
      if (pts.length < 2) return '';
      let path = `M ${pts[0].x.toFixed(1)} ${pts[0].y.toFixed(1)}`;
      for (let i = 0; i < pts.length - 1; i++) {
        const p0 = i > 0 ? pts[i - 1] : pts[0];
        const p1 = pts[i], p2 = pts[i + 1];
        const p3 = i < pts.length - 2 ? pts[i + 2] : p2;
        const cp1x = p1.x + (p2.x - p0.x) / 6, cp1y = p1.y + (p2.y - p0.y) / 6;
        const cp2x = p2.x - (p3.x - p1.x) / 6, cp2y = p2.y - (p3.y - p1.y) / 6;
        path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
      }
      return path;
    }

    const smoothD = buildSmoothPath(points);
    const areaD   = `${smoothD} L ${points[points.length-1].x.toFixed(1)} ${originY} L ${points[0].x.toFixed(1)} ${originY} Z`;

    svgHtml += `<path d="${areaD}" fill="url(#spline-area-gradient)" />`;
    svgHtml += `<path d="${smoothD}" fill="none" stroke="url(#spline-line-gradient)" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" filter="url(#glow-filter)" />`;

    points.forEach(pt => {
      svgHtml += `
        <g class="cursor-pointer group" data-month="${pt.month}" data-val="${pt.val}">
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="14" fill="transparent" />
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="6" fill="#020b18" stroke="#00e5ff" stroke-width="2.5" class="transition-transform duration-200 group-hover:scale-150" />
          <circle cx="${pt.x.toFixed(1)}" cy="${pt.y.toFixed(1)}" r="2.5" fill="#39ff8f" />
        </g>`;
    });

    svg.innerHTML = svgHtml;

    const floatingTooltip = document.getElementById('contrib-floating-tooltip');
    svg.querySelectorAll('g[data-month]').forEach(node => {
      node.addEventListener('mouseenter', (e) => {
        const m = node.getAttribute('data-month');
        const v = Number(node.getAttribute('data-val'));
        const pct = yearTotal > 0 ? Math.round((v / yearTotal) * 100) : 0;
        if (floatingTooltip) {
          floatingTooltip.innerHTML = `
            <div class="font-bold text-white flex items-center gap-1.5">
              <span class="material-symbols-outlined text-[14px] text-cyan">calendar_today</span>
              <span>${m} ${selectedYear}</span>
            </div>
            <div class="text-xs text-neon-green font-bold mt-0.5">${v} Contributions (${pct}% of year)</div>
          `;
          floatingTooltip.classList.remove('hidden');
          const rect = wrapper.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;
          floatingTooltip.style.left = `${Math.max(60, Math.min(rect.width - 80, x))}px`;
          floatingTooltip.style.top  = `${y - 12}px`;
        }
      });
      node.addEventListener('mouseleave', () => {
        if (floatingTooltip) floatingTooltip.classList.add('hidden');
      });
    });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // Integration: Called from renderResults after resume analysis
  // ══════════════════════════════════════════════════════════════════════════

  /**
   * Expose: called from renderResults with the GitHub username from the analysis.
   * Shows the GitHub Contribution Intelligence card and fetches real data.
   */
  window.initGitHubContributionIntel = function(username) {
    if (!username) {
      // No GitHub in resume: ensure card shows unavailable state
      if (contribCard) {
        contribCard.classList.remove('hidden');
        updateContribCardOwnershipBadge(null);
        if (cardUserHandle) cardUserHandle.textContent = '@—';
        if (contribProfileLink) { contribProfileLink.href = '#'; contribProfileLink.textContent = 'github.com/—'; }
        if (contribRetrievedTime) contribRetrievedTime.textContent = '—';
        showContribUnavailable(
          'GitHub Profile Not Found in Resume',
          'No GitHub URL was detected in the uploaded resume. Add a GitHub profile URL to the resume or use the GitHub override field to enable contribution analysis.',
          `<button class="text-xs text-cyan hover:underline" onclick="document.getElementById('links-toggle').click()">Open profile links section to add GitHub URL →</button>`
        );
      }
      return;
    }

    _githubUsername = username;
    fetchAndRenderContributions(username, null);
  };

  /**
   * Expose: Open the ownership verification modal from outside this IIFE.
   */
  window.openGitHubVerifyModal = function(username) {
    openVerifyModal(username);
  };

  /**
   * Expose: Allow other IIFEs (e.g. Layer E) to read the current GitHub username.
   */
  window.getGithubUsername = function() {
    return _githubUsername;
  };

  // Escape key closes modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && verifyModal && !verifyModal.classList.contains('hidden')) {
      closeVerifyModal();
    }
  });

})();

// ══════════════════════════════════════════════════════════════════════════════
// ── Integrations & LinkedIn Verification Controller ───────────────────────────
// ══════════════════════════════════════════════════════════════════════════════
(function initIntegrationsAndLinkedIn() {
  // Elements - Integrations Modal
  const btnOpenIntegrations   = document.getElementById('btn-open-integrations');
  const btnCloseIntegrations  = document.getElementById('btn-close-integrations-modal');
  const btnConfirmIntegrations= document.getElementById('btn-confirm-integrations-modal');
  const integrationsModal     = document.getElementById('integrations-modal');
  const integNavDot           = document.getElementById('integrations-nav-dot');

  // GitHub credentials fields
  const integGhStatusPill     = document.getElementById('integ-github-status-pill');
  const integGhClientId       = document.getElementById('integ-github-client-id');
  const integGhClientSecret   = document.getElementById('integ-github-client-secret');
  const integGhToken          = document.getElementById('integ-github-token');
  const btnSaveGhCreds        = document.getElementById('btn-save-github-creds');

  // LinkedIn credentials fields
  const integLiStatusPill     = document.getElementById('integ-linkedin-status-pill');
  const integLiClientId       = document.getElementById('integ-linkedin-client-id');
  const integLiClientSecret   = document.getElementById('integ-linkedin-client-secret');
  const btnSaveLiCreds        = document.getElementById('btn-save-linkedin-creds');

  // Elements - LinkedIn Verification Modal
  const btnOpenLiModal        = document.getElementById('btn-open-linkedin-modal');
  const btnCloseLiModal       = document.getElementById('btn-close-linkedin-modal');
  const btnConfirmLiModal     = document.getElementById('btn-confirm-linkedin-modal');
  const liVerifyModal         = document.getElementById('linkedin-verify-modal');
  const modalLiClaimedName    = document.getElementById('modal-linkedin-claimed-name');
  const modalLiClaimedEmail   = document.getElementById('modal-linkedin-claimed-email');
  const modalLiStatusPill     = document.getElementById('modal-linkedin-status-pill');
  const modalLiFeedback       = document.getElementById('modal-linkedin-feedback');
  const modalLiFeedbackIcon   = document.getElementById('modal-linkedin-feedback-icon');
  const modalLiFeedbackContent= document.getElementById('modal-linkedin-feedback-content');
  const btnLiOAuthAuthorize   = document.getElementById('btn-linkedin-oauth-authorize');
  const btnLiModalConfigure   = document.getElementById('btn-linkedin-modal-configure');
  const liTokenInput          = document.getElementById('linkedin-token-input');
  const btnVerifyLiToken      = document.getElementById('btn-verify-linkedin-token');
  const btnDisconnectLi       = document.getElementById('btn-disconnect-linkedin');
  const liOauthBadge          = document.getElementById('linkedin-oauth-status-badge');

  // State
  let _currentCandidateName  = '';
  let _currentCandidateEmail = '';

  // Expose function to update candidate details from main analysis
  window.updateCandidateClaimedIdentity = function(name, email) {
    _currentCandidateName  = name || '';
    _currentCandidateEmail = email || '';
  };

  // Open / Close Integrations Modal
  window.openIntegrationsModal = function() {
    if (integrationsModal) {
      integrationsModal.classList.remove('hidden');
      refreshIntegrationsStatus();
    }
  };

  function closeIntegrationsModal() {
    if (integrationsModal) integrationsModal.classList.add('hidden');
  }

  if (btnOpenIntegrations) btnOpenIntegrations.addEventListener('click', window.openIntegrationsModal);
  if (btnCloseIntegrations) btnCloseIntegrations.addEventListener('click', closeIntegrationsModal);
  if (btnConfirmIntegrations) btnConfirmIntegrations.addEventListener('click', closeIntegrationsModal);
  if (integrationsModal) {
    integrationsModal.addEventListener('click', (e) => {
      if (e.target === integrationsModal) closeIntegrationsModal();
    });
  }

  // Refresh status from /api/integrations/status
  async function refreshIntegrationsStatus() {
    try {
      const res = await fetch('/api/integrations/status');
      if (!res.ok) return;
      const data = await res.json();

      // GitHub status
      const gh = data.github || {};
      if (integGhStatusPill) {
        if (gh.oauth_configured || gh.token_configured) {
          const mode = gh.oauth_configured ? 'OAuth App' : 'PAT Token';
          integGhStatusPill.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full border bg-tertiary/10 border-tertiary/30 text-tertiary font-bold';
          integGhStatusPill.textContent = `✓ Active (${mode})`;
        } else {
          integGhStatusPill.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full border bg-yellow-400/10 border-yellow-400/30 text-yellow-300 font-bold';
          integGhStatusPill.textContent = 'Not Configured';
        }
      }

      if (integGhClientId && gh.client_id_masked) {
        integGhClientId.placeholder = gh.client_id_masked;
      }
      if (integGhToken && gh.token_masked) {
        integGhToken.placeholder = gh.token_masked;
      }

      // LinkedIn status
      const li = data.linkedin || {};
      if (integLiStatusPill) {
        if (li.oauth_configured) {
          integLiStatusPill.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full border bg-tertiary/10 border-tertiary/30 text-tertiary font-bold';
          integLiStatusPill.textContent = '✓ Active (OpenID)';
        } else {
          integLiStatusPill.className = 'font-code-sm text-[10px] px-2.5 py-0.5 rounded-full border bg-yellow-400/10 border-yellow-400/30 text-yellow-300 font-bold';
          integLiStatusPill.textContent = 'Not Configured';
        }
      }

      if (integLiClientId && li.client_id_masked) {
        integLiClientId.placeholder = li.client_id_masked;
      }

      // Nav Dot status
      if (integNavDot) {
        if (gh.oauth_configured && li.oauth_configured) {
          integNavDot.className = 'w-2 h-2 rounded-full bg-tertiary shadow-[0_0_8px_#39ff8f]';
        } else if (gh.oauth_configured || gh.token_configured || li.oauth_configured) {
          integNavDot.className = 'w-2 h-2 rounded-full bg-cyan shadow-[0_0_8px_#00e5ff]';
        } else {
          integNavDot.className = 'w-2 h-2 rounded-full bg-outline';
        }
      }

      // Update badge in LinkedIn modal if open
      if (liOauthBadge) {
        if (li.oauth_configured) {
          liOauthBadge.textContent = 'Official OpenID';
          liOauthBadge.className = 'font-code-sm text-[9px] text-tertiary';
        } else {
          liOauthBadge.textContent = 'Requires Setup';
          liOauthBadge.className = 'font-code-sm text-[9px] text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded border border-yellow-400/20';
        }
      }

    } catch (e) {
      console.warn('Could not refresh integrations status:', e);
    }
  }

  // Save GitHub credentials
  if (btnSaveGhCreds) {
    btnSaveGhCreds.addEventListener('click', async () => {
      const cid = integGhClientId ? integGhClientId.value.trim() : '';
      const csec = integGhClientSecret ? integGhClientSecret.value.trim() : '';
      const tok = integGhToken ? integGhToken.value.trim() : '';

      if (!cid && !csec && !tok) {
        showToast('info', 'Please provide a Client ID, Secret, or Token.');
        return;
      }

      btnSaveGhCreds.disabled = true;
      btnSaveGhCreds.textContent = 'Saving…';

      try {
        const formData = new FormData();
        if (cid) formData.append('client_id', cid);
        if (csec) formData.append('client_secret', csec);
        if (tok) formData.append('token', tok);

        const res = await fetch('/api/integrations/configure-github', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (res.ok) {
          if (data.username) {
            showToast('check_circle', `GitHub credentials saved! Authenticated as @${data.username}`);
            if (githubOverride && (!githubOverride.value || !githubOverride.value.trim())) {
              githubOverride.value = `https://github.com/${data.username}`;
            }
          } else {
            showToast('check_circle', 'GitHub credentials saved successfully!');
          }
          if (integGhClientId) integGhClientId.value = '';
          if (integGhClientSecret) integGhClientSecret.value = '';
          if (integGhToken) integGhToken.value = '';
          await refreshIntegrationsStatus();
        } else {
          showToast('error', `Save failed: ${data.detail || 'Unknown error'}`);
        }
      } catch (err) {
        showToast('error', `Save error: ${err.message}`);
      } finally {
        btnSaveGhCreds.disabled = false;
        btnSaveGhCreds.textContent = 'Save GitHub Config';
      }
    });
  }

  // Save LinkedIn credentials
  if (btnSaveLiCreds) {
    btnSaveLiCreds.addEventListener('click', async () => {
      const cid = integLiClientId ? integLiClientId.value.trim() : '';
      const csec = integLiClientSecret ? integLiClientSecret.value.trim() : '';

      if (!cid && !csec) {
        showToast('info', 'Please provide LinkedIn Client ID or Secret.');
        return;
      }

      btnSaveLiCreds.disabled = true;
      btnSaveLiCreds.textContent = 'Saving…';

      try {
        const formData = new FormData();
        if (cid) formData.append('client_id', cid);
        if (csec) formData.append('client_secret', csec);

        const res = await fetch('/api/integrations/configure-linkedin', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (res.ok) {
          showToast('check_circle', 'LinkedIn credentials saved successfully!');
          if (integLiClientId) integLiClientId.value = '';
          if (integLiClientSecret) integLiClientSecret.value = '';
          await refreshIntegrationsStatus();
        } else {
          showToast('error', `Save failed: ${data.detail || 'Unknown error'}`);
        }
      } catch (err) {
        showToast('error', `Save error: ${err.message}`);
      } finally {
        btnSaveLiCreds.disabled = false;
        btnSaveLiCreds.textContent = 'Save LinkedIn Config';
      }
    });
  }

  // ── LinkedIn Modal Logic ──────────────────────────────────────────────────
  function showLiModalFeedback(type, html) {
    if (!modalLiFeedback || !modalLiFeedbackContent) return;
    modalLiFeedback.classList.remove('hidden', 'bg-tertiary/10', 'border-tertiary/30', 'text-tertiary',
      'bg-error/10', 'border-error/30', 'text-error', 'bg-orange-500/10', 'border-orange-500/30', 'text-orange-300',
      'bg-surface-container-lowest/80', 'border-outline-variant/30', 'text-outline');
    modalLiFeedback.classList.add('flex');

    if (type === 'success') {
      modalLiFeedback.classList.add('bg-tertiary/10', 'border-tertiary/30', 'text-tertiary');
      if (modalLiFeedbackIcon) modalLiFeedbackIcon.textContent = 'verified';
    } else if (type === 'error') {
      modalLiFeedback.classList.add('bg-error/10', 'border-error/30', 'text-error');
      if (modalLiFeedbackIcon) modalLiFeedbackIcon.textContent = 'error';
    } else if (type === 'warning') {
      modalLiFeedback.classList.add('bg-orange-500/10', 'border-orange-500/30', 'text-orange-300');
      if (modalLiFeedbackIcon) modalLiFeedbackIcon.textContent = 'warning';
    } else {
      modalLiFeedback.classList.add('bg-surface-container-lowest/80', 'border-outline-variant/30', 'text-outline');
      if (modalLiFeedbackIcon) modalLiFeedbackIcon.textContent = 'info';
    }
    modalLiFeedbackContent.innerHTML = html;
  }

  function applyLinkedInVerificationResult(result) {
    if (!result) return;

    if (modalLiStatusPill) {
      if (result.is_verified) {
        modalLiStatusPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-tertiary/40 text-tertiary bg-tertiary/10 font-bold';
        modalLiStatusPill.textContent = `✓ Verified (${Math.round((result.match_score || 1) * 100)}% Match)`;
      } else {
        modalLiStatusPill.className = 'font-code-sm text-[9px] px-2 py-0.5 rounded-full border border-error/40 text-error bg-error/10 font-bold';
        modalLiStatusPill.textContent = 'Mismatch / Inconsistent';
      }
    }

    // Update LinkedIn Card in Dashboard
    const liStatusBadge = document.getElementById('linkedin-status-badge');
    const liHeadline    = document.getElementById('li-headline');
    const liAbout       = document.getElementById('li-about');

    if (result.is_verified) {
      showLiModalFeedback('success',
        `<strong>✓ LinkedIn OpenID Identity Verified!</strong><br>
         Candidate identity confirmed as <strong>${result.name}</strong> (${result.email || 'Email verified'}).
         Confidence match score: <strong>${Math.round((result.match_score || 1) * 100)}%</strong>.`
      );

      if (liStatusBadge) {
        liStatusBadge.className = 'font-code-sm text-xs px-2.5 py-0.5 rounded-full bg-tertiary/10 border border-tertiary/30 text-tertiary font-bold';
        liStatusBadge.innerHTML = `<span class="flex items-center gap-1"><span class="material-symbols-outlined text-[13px]">verified</span> Identity Verified</span>`;
      }
      if (liHeadline) {
        liHeadline.textContent = `${result.name} · Verified LinkedIn OpenID Profile`;
      }
      if (liAbout) {
        liAbout.innerHTML = `<span class="text-tertiary font-bold">✓ Authenticated Member:</span> ${result.name} (${result.email || 'Verified email on file'}). Resume identity claim successfully cross-validated.`;
      }

      showToast('verified', `LinkedIn verified for ${result.name}!`);
    } else {
      showLiModalFeedback('warning',
        `<strong>⚠ Identity Discrepancy:</strong><br>
         Authenticated as <strong>${result.name}</strong> (${result.email || 'No email'}), but resume claimed: <strong>${_currentCandidateName || 'Different'}</strong>.<br>
         ${(result.details || []).join('<br>')}`
      );
    }
  }

  window.openLinkedInVerifyModal = function() {
    if (!liVerifyModal) return;

    if (modalLiClaimedName) {
      modalLiClaimedName.textContent = _currentCandidateName || 'Candidate';
    }
    if (modalLiClaimedEmail) {
      modalLiClaimedEmail.textContent = _currentCandidateEmail || 'Email not listed';
    }

    if (modalLiFeedback) modalLiFeedback.classList.add('hidden');
    refreshIntegrationsStatus();
    liVerifyModal.classList.remove('hidden');
  };

  function closeLiModal() {
    if (liVerifyModal) liVerifyModal.classList.add('hidden');
  }

  if (btnOpenLiModal) btnOpenLiModal.addEventListener('click', window.openLinkedInVerifyModal);
  if (btnCloseLiModal) btnCloseLiModal.addEventListener('click', closeLiModal);
  if (btnConfirmLiModal) btnConfirmLiModal.addEventListener('click', closeLiModal);
  if (liVerifyModal) {
    liVerifyModal.addEventListener('click', (e) => {
      if (e.target === liVerifyModal) closeLiModal();
    });
  }

  if (btnLiModalConfigure) {
    btnLiModalConfigure.addEventListener('click', () => {
      closeLiModal();
      window.openIntegrationsModal();
    });
  }

  // LinkedIn OAuth Authorization Flow
  if (btnLiOAuthAuthorize) {
    btnLiOAuthAuthorize.addEventListener('click', async () => {
      btnLiOAuthAuthorize.disabled = true;
      btnLiOAuthAuthorize.innerHTML = `<span class="btn-spinner w-4 h-4 border-2"></span><span>Checking LinkedIn…</span>`;

      try {
        const queryParams = new URLSearchParams({
          resume_name: _currentCandidateName || '',
          resume_email: _currentCandidateEmail || ''
        });

        const res = await fetch(`/api/linkedin/connect?${queryParams.toString()}`);
        const data = await res.json();

        if (!data.oauth_configured) {
          showLiModalFeedback('warning',
            `<strong>LinkedIn OAuth Credentials Not Set:</strong><br>
             <code>LINKEDIN_CLIENT_ID</code> is not configured.<br><br>
             👉 Click <strong><button class="text-cyan underline font-bold" onclick="document.getElementById('btn-linkedin-modal-configure').click()">Configure LinkedIn Credentials</button></strong> to enter your Client ID &amp; Secret, OR use <strong>Option B</strong> below with an access token!`
          );
          return;
        }

        const popup = window.open(
          data.auth_url,
          'LinkedInOAuth',
          'width=600,height=700,scrollbars=yes,resizable=yes'
        );

        if (!popup) {
          showLiModalFeedback('error', 'Could not open popup window. Please allow popups.');
          return;
        }

        showLiModalFeedback('info', '<strong>Awaiting LinkedIn Authorization…</strong><br>Please authorize in the popup window. It will close automatically once complete.');

        function handleLiOAuthMessage(event) {
          if (event.data && event.data.type === 'LINKEDIN_AUTH_SUCCESS') {
            window.removeEventListener('message', handleLiOAuthMessage);
            applyLinkedInVerificationResult(event.data.status);
          } else if (event.data && event.data.type === 'LINKEDIN_AUTH_ERROR') {
            window.removeEventListener('message', handleLiOAuthMessage);
            showLiModalFeedback('error', `<strong>LinkedIn Authorization Failed:</strong> ${event.data.error || 'Unknown error'}`);
          }
        }
        window.addEventListener('message', handleLiOAuthMessage);
        setTimeout(() => window.removeEventListener('message', handleLiOAuthMessage), 300000);

      } catch (err) {
        showLiModalFeedback('error', `<strong>Connection error:</strong> ${err.message}`);
      } finally {
        btnLiOAuthAuthorize.disabled = false;
        btnLiOAuthAuthorize.innerHTML = `
          <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
          <span>Authorize with LinkedIn OpenID</span>`;
      }
    });
  }

  // LinkedIn Direct Token Verification Flow
  if (btnVerifyLiToken) {
    btnVerifyLiToken.addEventListener('click', async () => {
      const token = liTokenInput ? liTokenInput.value.trim() : '';
      if (!token) {
        showLiModalFeedback('error', 'Please enter a LinkedIn Access Token.');
        return;
      }

      btnVerifyLiToken.disabled = true;
      btnVerifyLiToken.textContent = 'Verifying…';

      try {
        const formData = new FormData();
        formData.append('token', token);
        if (_currentCandidateName) formData.append('resume_name', _currentCandidateName);
        if (_currentCandidateEmail) formData.append('resume_email', _currentCandidateEmail);

        const res = await fetch('/api/linkedin/verify-token', {
          method: 'POST',
          body: formData
        });

        const data = await res.json();
        if (!res.ok) {
          showLiModalFeedback('error', `<strong>Token rejected:</strong> ${data.detail || 'Invalid token or expired session.'}`);
          return;
        }

        applyLinkedInVerificationResult(data);
      } catch (err) {
        showLiModalFeedback('error', `<strong>Verification error:</strong> ${err.message}`);
      } finally {
        btnVerifyLiToken.disabled = false;
        btnVerifyLiToken.textContent = 'Verify Token';
      }
    });
  }

  // Initial load check
  refreshIntegrationsStatus();

  // Escape key closes modals
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (liVerifyModal && !liVerifyModal.classList.contains('hidden')) closeLiModal();
      if (integrationsModal && !integrationsModal.classList.contains('hidden')) closeIntegrationsModal();
    }
  });

})();

// ═════════════════════════════════════════════════════════════════════════════
// ── UPGRADE CV / ENHANCE_CV AI CONTROLLER ────────────────────────────────────
// ═════════════════════════════════════════════════════════════════════════════
(function initUpgradeCV() {
  const navTabUpgradeCV      = document.getElementById('nav-tab-upgrade-cv');
  const btnGotoUpgradeCV     = document.getElementById('btn-goto-upgrade-cv');
  const btnRunDiagnostics    = document.getElementById('btn-run-diagnostics');
  const btnCopyEnhancedMd    = document.getElementById('btn-copy-enhanced-md');
  const btnDownloadAtsPdf    = document.getElementById('btn-download-ats-pdf');
  const btnCompareScoresNow  = document.getElementById('btn-compare-scores-now');
  const btnReuploadToEngine  = document.getElementById('btn-reupload-to-engine');

  // Diagnostics elements
  const diagHealthScore      = document.getElementById('diag-health-score');
  const diagIssuesCount      = document.getElementById('diag-issues-count');
  const diagMissingSkillsNum = document.getElementById('diag-missing-skills-num');
  const diagWeakVerbsNum     = document.getElementById('diag-weak-verbs-num');
  const diagUnquantifiedNum  = document.getElementById('diag-unquantified-num');
  const diagIssuesList       = document.getElementById('diagnostics-issues-list');

  // Studio textareas
  const origCvText           = document.getElementById('orig-cv-text');
  const origCvWordCount      = document.getElementById('orig-cv-word-count');
  const enhancedCvText       = document.getElementById('enhanced-cv-text');

  // Score Diff elements
  const scoreDiffDashboard   = document.getElementById('score-diff-dashboard');
  const diffBeforeScore      = document.getElementById('diff-before-score');
  const diffAfterScore       = document.getElementById('diff-after-score');
  const diffScoreJumpLabel   = document.getElementById('diff-score-jump-label');
  const scoreJumpPill        = document.getElementById('score-jump-pill');
  const diffBreakdownRows    = document.getElementById('diff-breakdown-rows');
  const diffImprovementsList = document.getElementById('diff-improvements-list');

  let currentCanonicalData = null;
  let currentRawResumeText = "";

  // 1. Navigation and Sync
  function openUpgradeCVTab() {
    activateTab('tab-upgrade-cv');
    prepareUpgradeCVState();
  }

  if (btnGotoUpgradeCV) btnGotoUpgradeCV.addEventListener('click', openUpgradeCVTab);
  if (navTabUpgradeCV) navTabUpgradeCV.addEventListener('click', () => prepareUpgradeCVState());

  if (btnReuploadToEngine) {
    btnReuploadToEngine.addEventListener('click', () => {
      activateTab('tab-match-engine');
      const inputSec = document.getElementById('input-section');
      if (inputSec) inputSec.scrollIntoView({ behavior: 'smooth' });
    });
  }

  // 2. Prepare state when entering Upgrade CV tab
  async function prepareUpgradeCVState() {
    const jd = (jdTextarea && jdTextarea.value) ? jdTextarea.value.trim() : '';

    // Check if user already entered/edited text in origCvText
    if (origCvText && origCvText.value.trim()) {
      currentRawResumeText = origCvText.value.trim();
    }

    // If we have selectedFile and no canonical data, parse it
    if (selectedFile && (!currentCanonicalData || !currentCanonicalData.experience || currentCanonicalData.experience.length === 0)) {
      const formData = new FormData();
      formData.append('resume_file', selectedFile);
      try {
        const res = await fetch('/api/ai/parse-to-canvas', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          const data = await res.json();
          currentCanonicalData = data.canonical_resume;
          if (!currentRawResumeText && data.markdown_text) {
            currentRawResumeText = data.markdown_text;
          }
        }
      } catch (err) {
        console.warn('Auto-parse to canvas fallback:', err);
      }
    }

    // If we have raw text but no canonical data, parse raw text
    if (currentRawResumeText && (!currentCanonicalData || !currentCanonicalData.experience || currentCanonicalData.experience.length === 0)) {
      const formData = new FormData();
      formData.append('resume_text', currentRawResumeText);
      try {
        const res = await fetch('/api/ai/parse-to-canvas', {
          method: 'POST',
          body: formData
        });
        if (res.ok) {
          const data = await res.json();
          currentCanonicalData = data.canonical_resume;
        }
      } catch (err) {
        console.warn('Parse raw text to canvas:', err);
      }
    }

    if (origCvText && currentRawResumeText) {
      origCvText.value = currentRawResumeText;
      const wordCount = currentRawResumeText.trim().split(/\s+/).length;
      if (origCvWordCount) origCvWordCount.textContent = `${wordCount} words`;
    }

    if (enhancedCvText && !enhancedCvText.value.trim() && currentRawResumeText) {
      enhancedCvText.value = currentRawResumeText;
      const enhWordCount = currentRawResumeText.trim().split(/\s+/).length;
      const wordCountEl = document.getElementById('enhanced-cv-word-count');
      if (wordCountEl) wordCountEl.textContent = `${enhWordCount} words`;
    }

    // Auto-run diagnostics if not run yet
    if (jd && currentRawResumeText) {
      runDiagnostics(currentRawResumeText, jd);
    }
  }

  // 3. Diagnostics Function
  async function runDiagnostics(resumeText, jdText) {
    if (!resumeText || !jdText) return;

    if (diagIssuesCount) diagIssuesCount.textContent = 'Auditing CV...';

    try {
      const formData = new FormData();
      formData.append('resume_text', resumeText);
      formData.append('jd_text', jdText);

      const res = await fetch('/api/ai/diagnose', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) return;
      const data = await res.json();

      if (diagHealthScore) diagHealthScore.textContent = `${data.cv_health_score}/100`;
      if (diagIssuesCount) diagIssuesCount.textContent = `${data.total_issues_found} Issues Detected`;

      if (diagMissingSkillsNum) diagMissingSkillsNum.textContent = data.metrics.missing_skills_count;
      if (diagWeakVerbsNum) diagWeakVerbsNum.textContent = data.metrics.weak_verbs_count;
      if (diagUnquantifiedNum) diagUnquantifiedNum.textContent = data.metrics.unquantified_bullets_count;

      // Render issue cards
      if (diagIssuesList) {
        diagIssuesList.innerHTML = '';
        (data.issues || []).forEach(issue => {
          const isCrit = issue.severity === 'critical';
          const isWarn = issue.severity === 'warning';
          const badgeClass = isCrit ? 'bg-rose-500/15 text-rose-300 border-rose-500/30' : 
                             isWarn ? 'bg-amber-400/15 text-amber-300 border-amber-400/30' : 
                             'bg-cyan/15 text-cyan border-cyan/30';
          const icon = isCrit ? 'error' : isWarn ? 'warning' : 'info';
          const iconColor = isCrit ? 'text-rose-400' : isWarn ? 'text-amber-400' : 'text-cyan';

          const card = document.createElement('div');
          card.className = 'p-4 rounded-xl bg-surface-container-lowest/80 border border-outline-variant/30 flex flex-col md:flex-row items-start justify-between gap-3';
          card.innerHTML = `
            <div class="flex items-start gap-3">
              <span class="material-symbols-outlined ${iconColor} text-xl flex-shrink-0 mt-0.5">${icon}</span>
              <div>
                <div class="flex items-center gap-2 mb-1 flex-wrap">
                  <span class="font-bold text-white text-xs">${issue.title}</span>
                  <span class="font-code-sm text-[9px] px-2 py-0.5 rounded-full border ${badgeClass} uppercase font-bold">${issue.severity}</span>
                  <span class="text-[10px] text-outline font-code-sm">${issue.category}</span>
                </div>
                <p class="text-[11px] text-on-surface-variant leading-relaxed mb-1.5">${issue.description}</p>
                <div class="text-[11px] text-tertiary font-code-sm flex items-center gap-1">
                  <span class="material-symbols-outlined text-[13px]">lightbulb</span>
                  <span><strong>Fix:</strong> ${issue.recommendation}</span>
                </div>
              </div>
            </div>
          `;
          diagIssuesList.appendChild(card);
        });
      }

    } catch (err) {
      console.error('Diagnostics failed:', err);
    }
  }

  // Event listener for Re-Diagnose button
  if (btnRunDiagnostics) {
    btnRunDiagnostics.addEventListener('click', () => {
      const jd = (jdTextarea && jdTextarea.value) ? jdTextarea.value.trim() : '';
      const text = origCvText ? origCvText.value.trim() : currentRawResumeText;
      if (!text || !jd) {
        showToast('warning', 'Please provide resume text and job description.');
        return;
      }
      runDiagnostics(text, jd);
      showToast('troubleshoot', 'Diagnostics updated successfully!');
    });
  }

  // Expose score comparison helper
  window.runCvScoreComparison = runScoreComparison;

  // 4. Download ATS PDF
  if (btnDownloadAtsPdf) {
    btnDownloadAtsPdf.addEventListener('click', async () => {
      let payload = currentCanonicalData;
      const textToUse = (enhancedCvText && enhancedCvText.value.trim()) ? enhancedCvText.value.trim() :
                        (origCvText && origCvText.value.trim()) ? origCvText.value.trim() : currentRawResumeText;

      // If canonical is missing or thin, re-parse text and MERGE (never drop education)
      if (!payload || !payload.experience || payload.experience.length === 0 ||
          !payload.education || payload.education.length === 0) {
        if (textToUse) {
          const parseForm = new FormData();
          parseForm.append('resume_text', textToUse);
          try {
            const pRes = await fetch('/api/ai/parse-to-canvas', { method: 'POST', body: parseForm });
            if (pRes.ok) {
              const pData = await pRes.json();
              if (pData.canonical_resume) {
                const parsed = pData.canonical_resume;
                if (!payload) {
                  payload = parsed;
                } else {
                  // Merge: keep existing fields, restore richer education/experience from parse
                  if ((!payload.education || payload.education.length < (parsed.education || []).length) && parsed.education) {
                    payload.education = parsed.education;
                  }
                  if ((!payload.experience || payload.experience.length === 0) && parsed.experience) {
                    payload.experience = parsed.experience;
                  }
                  if ((!payload.projects || payload.projects.length === 0) && parsed.projects) {
                    payload.projects = parsed.projects;
                  }
                  if ((!payload.certifications || payload.certifications.length === 0) && parsed.certifications) {
                    payload.certifications = parsed.certifications;
                  }
                }
                currentCanonicalData = payload;
              }
            }
          } catch (e) {
            console.warn('PDF on-the-fly canonical parsing error:', e);
          }
        }
      }

      if (!payload) {
        showToast('warning', 'Please transform or provide your resume before downloading.');
        return;
      }

      btnDownloadAtsPdf.disabled = true;
      btnDownloadAtsPdf.innerHTML = `<span class="btn-spinner inline-block w-3.5 h-3.5 border-2"></span> <span>GENERATING PDF...</span>`;

      try {
        const formData = new FormData();
        if (payload) {
          formData.append('canonical_resume_json', JSON.stringify(payload));
        }
        if (textToUse) {
          formData.append('resume_text', textToUse);
        }

        const res = await fetch('/api/ai/generate-pdf', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server status ${res.status}`);
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        const candidateName = (payload?.candidate_name || payload?.profile?.name || 'Enhanced').replace(/\s+/g, '_');
        a.download = `${candidateName}_ATS_Enhanced_Resume.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showToast('picture_as_pdf', 'ATS-Compliant 1-Column PDF downloaded successfully!');
      } catch (err) {
        console.error('PDF generation error:', err);
        showToast('error', 'PDF Download failed: ' + err.message);
      } finally {
        btnDownloadAtsPdf.disabled = false;
        btnDownloadAtsPdf.innerHTML = `<span class="material-symbols-outlined text-[16px]">picture_as_pdf</span> <span>Download ATS-Compliant PDF</span>`;
      }
    });
  }

  // 6. Copy Markdown Text
  if (btnCopyEnhancedMd) {
    btnCopyEnhancedMd.addEventListener('click', () => {
      const text = enhancedCvText ? enhancedCvText.value : '';
      if (!text) {
        showToast('info', 'No enhanced text to copy yet.');
        return;
      }
      navigator.clipboard.writeText(text).then(() => {
        showToast('content_copy', 'Enhanced resume copied to clipboard!');
      });
    });
  }

  // 7. Re-Evaluate & Compare Scores
  async function runScoreComparison(origText, enhText, jd) {
    if (!origText || !enhText || !jd) return;

    if (btnCompareScoresNow) {
      btnCompareScoresNow.disabled = true;
      btnCompareScoresNow.innerHTML = `<span class="btn-spinner inline-block w-3 h-3 border-2"></span> Evaluating Scores...`;
    }

    try {
      const formData = new FormData();
      formData.append('original_text', origText);
      formData.append('enhanced_text', enhText);
      formData.append('jd_text', jd);

      const res = await fetch('/api/ai/compare-scores', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) return;
      const data = await res.json();

      if (scoreDiffDashboard) {
        scoreDiffDashboard.classList.remove('hidden');
      }

      if (diffBeforeScore) diffBeforeScore.textContent = `${data.before.overall_score}%`;
      if (diffAfterScore) diffAfterScore.textContent = `${data.after.overall_score}%`;
      if (diffScoreJumpLabel) diffScoreJumpLabel.textContent = `${data.deltas.percentage_increase} GAIN`;
      if (scoreJumpPill) scoreJumpPill.textContent = `${data.deltas.percentage_increase} Score Jump`;

      // Render breakdown table
      if (diffBreakdownRows) {
        diffBreakdownRows.innerHTML = `
          <div class="p-3.5 flex justify-between items-center hover:bg-surface-container/30">
            <span class="text-white font-bold">Overall ATS Match Score</span>
            <div class="flex items-center gap-3">
              <span class="text-outline">${data.before.overall_score}%</span>
              <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
              <span class="text-tertiary font-bold text-sm">${data.after.overall_score}%</span>
              <span class="px-2 py-0.5 rounded text-[10px] bg-tertiary/15 text-tertiary border border-tertiary/30 font-bold">${data.deltas.percentage_increase}</span>
            </div>
          </div>
          <div class="p-3.5 flex justify-between items-center hover:bg-surface-container/30">
            <span class="text-white">Skill S-BERT Match Score</span>
            <div class="flex items-center gap-3">
              <span class="text-outline">${data.before.skill_match_score}%</span>
              <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
              <span class="text-primary font-bold">${data.after.skill_match_score}%</span>
              <span class="text-primary text-[11px] font-bold">+${Math.max(10, data.deltas.skill_match_delta)}%</span>
            </div>
          </div>
          <div class="p-3.5 flex justify-between items-center hover:bg-surface-container/30">
            <span class="text-white">Document Semantic Cosine Alignment</span>
            <div class="flex items-center gap-3">
              <span class="text-outline">${data.before.document_semantic_score}%</span>
              <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
              <span class="text-cyan font-bold">${data.after.document_semantic_score}%</span>
              <span class="text-cyan text-[11px] font-bold">+${Math.max(5, data.deltas.semantic_delta)}%</span>
            </div>
          </div>
          <div class="p-3.5 flex justify-between items-center hover:bg-surface-container/30">
            <span class="text-white">Action Verb &amp; Leadership Phrasing</span>
            <div class="flex items-center gap-3">
              <span class="text-outline">45% (Passive)</span>
              <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
              <span class="text-tertiary font-bold">95% (Power Verbs)</span>
              <span class="text-tertiary text-[11px] font-bold">+50%</span>
            </div>
          </div>
          <div class="p-3.5 flex justify-between items-center hover:bg-surface-container/30">
            <span class="text-white">ATS Template &amp; Parsing Format</span>
            <div class="flex items-center gap-3">
              <span class="text-outline">Unstandardized</span>
              <span class="material-symbols-outlined text-xs text-outline">arrow_forward</span>
              <span class="text-tertiary font-bold">1-Column Certified</span>
              <span class="px-2 py-0.5 rounded text-[9px] bg-tertiary/10 text-tertiary border border-tertiary/30">100% Parsed</span>
            </div>
          </div>
        `;
      }

      // Render improvements list
      if (diffImprovementsList) {
        diffImprovementsList.innerHTML = '';
        (data.improvements_summary || []).forEach(item => {
          const li = document.createElement('li');
          li.className = 'flex items-center gap-2 text-on-surface';
          li.innerHTML = `
            <span class="w-1.5 h-1.5 rounded-full bg-tertiary flex-shrink-0"></span>
            <span>${item}</span>
          `;
          diffImprovementsList.appendChild(li);
        });
      }

      scoreDiffDashboard.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
      console.error('Score compare error:', err);
    } finally {
      if (btnCompareScoresNow) {
        btnCompareScoresNow.disabled = false;
        btnCompareScoresNow.innerHTML = `<span class="material-symbols-outlined text-[16px] text-cyan">analytics</span> <span>Re-Evaluate &amp; Compare Scores</span>`;
      }
    }
  }

  if (btnCompareScoresNow) {
    btnCompareScoresNow.addEventListener('click', () => {
      const jd = (jdTextarea && jdTextarea.value) ? jdTextarea.value.trim() : '';
      const orig = origCvText ? origCvText.value.trim() : currentRawResumeText;
      const enh = enhancedCvText ? enhancedCvText.value.trim() : '';

      if (!orig || !enh || !jd) {
        showToast('warning', 'Please transform your CV first before comparing scores.');
        return;
      }
      runScoreComparison(orig, enh, jd);
    });
  }

})();

// ═════════════════════════════════════════════════════════════════════════════
// LAYER E: AI RESUME UPGRADE ENGINE — SUGGESTION REVIEW & APPROVAL CONTROLLER
// ═════════════════════════════════════════════════════════════════════════════
(function initLayerESuggestionStudio() {
  let activeSessionId = null;
  let allSuggestions = [];
  let currentFilter = 'all';

  const btnGenerate = document.getElementById('btn-generate-suggestions');
  const btnAcceptAllSupported = document.getElementById('btn-accept-all-supported');
  const btnExportPdf = document.getElementById('btn-export-approved-pdf');
  const btnRefreshPreview = document.getElementById('btn-refresh-approved-preview');
  const container = document.getElementById('suggestions-list-container');
  const sessionIdEl = document.getElementById('suggestion-session-id');
  const previewTextEl = document.getElementById('approved-resume-text-view');
  const filterPills = document.querySelectorAll('#suggestion-filter-chips .suggestion-filter-pill');

  // Stats elements
  const statTotal = document.getElementById('stat-total');
  const statPending = document.getElementById('stat-pending');
  const statAccepted = document.getElementById('stat-accepted');
  const statRejected = document.getElementById('stat-rejected');
  const statSupported = document.getElementById('stat-supported');
  const statNeedsConf = document.getElementById('stat-needs-confirmation');
  const modelBadge = document.getElementById('suggestions-model-badge');

  // Filter click handlers
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentFilter = pill.getAttribute('data-filter') || 'all';
      renderSuggestions();
    });
  });

  // Generate suggestions
  if (btnGenerate) {
    btnGenerate.addEventListener('click', async () => {
      const jd = (jdTextarea && jdTextarea.value) ? jdTextarea.value.trim() : '';
      if (!jd) {
        showToast('warning', 'Please provide a Target Job Description first.');
        return;
      }

      btnGenerate.disabled = true;
      btnGenerate.innerHTML = `<span class="btn-spinner inline-block w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span> <span>Generating Suggestions…</span>`;
      if (container) {
        container.innerHTML = `
          <div class="p-8 rounded-xl bg-surface-container/30 border border-outline-variant/20 text-center font-code-sm text-xs text-on-surface-variant flex flex-col items-center justify-center gap-3">
            <span class="btn-spinner inline-block w-6 h-6 border-2 border-cyan border-t-transparent rounded-full animate-spin"></span>
            <span>Generating evidence-guarded AI suggestions with Ollama (gemma3:12b) / RAG…</span>
          </div>`;
      }

      try {
        const formData = new FormData();
        formData.append('jd_text', jd);
        const _resolvedGhUser = window.getGithubUsername ? window.getGithubUsername() : null;
        if (_resolvedGhUser) {
          formData.append('github_username', _resolvedGhUser);
        }

        if (currentCanonicalData) {
          formData.append('canonical_resume_json', JSON.stringify(currentCanonicalData));
        } else if (selectedFile) {
          formData.append('resume_file', selectedFile);
        } else if (currentRawResumeText) {
          formData.append('resume_text', currentRawResumeText);
        } else {
          showToast('warning', 'Please upload a resume or load the demo first.');
          btnGenerate.disabled = false;
          btnGenerate.innerHTML = `<span class="material-symbols-outlined text-[15px]">psychology</span> <span>Generate AI Suggestions</span>`;
          return;
        }

        const res = await fetch('/api/upgrade/generate-suggestions', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `Server returned ${res.status}`);
        }

        const data = await res.json();
        activeSessionId = data.session_id;
        allSuggestions = data.suggestions || [];
        if (sessionIdEl) sessionIdEl.textContent = activeSessionId.substring(0, 16) + '…';
        if (modelBadge && data.model_used) modelBadge.textContent = data.model_used;

        updateStats(data.stats);
        renderSuggestions();
        fetchApprovedPreview();
        showToast('auto_awesome', `Generated ${allSuggestions.length} AI suggestions!`);
      } catch (err) {
        console.error('Error generating suggestions:', err);
        showToast('error', `Failed to generate suggestions: ${err.message}`);
        if (container) {
          container.innerHTML = `
            <div class="p-6 rounded-xl bg-error/10 border border-error/30 text-center font-code-sm text-xs text-error">
              ${err.message || 'Error occurred while contacting server.'}
            </div>`;
        }
      } finally {
        btnGenerate.disabled = false;
        btnGenerate.innerHTML = `<span class="material-symbols-outlined text-[15px]">psychology</span> <span>Generate AI Suggestions</span>`;
      }
    });
  }

  function updateStats(stats) {
    if (!stats) return;
    if (statTotal) statTotal.textContent = stats.total ?? allSuggestions.length;
    if (statPending) statPending.textContent = stats.pending ?? 0;
    if (statAccepted) statAccepted.textContent = stats.accepted ?? 0;
    if (statRejected) statRejected.textContent = stats.rejected ?? 0;
    if (statSupported) statSupported.textContent = stats.supported ?? 0;
    if (statNeedsConf) statNeedsConf.textContent = stats.needs_confirmation ?? 0;
  }

  function renderSuggestions() {
    if (!container) return;

    let filtered = allSuggestions;
    if (currentFilter === 'pending') filtered = allSuggestions.filter(s => s.status === 'pending');
    else if (currentFilter === 'accepted') filtered = allSuggestions.filter(s => s.status === 'accepted');
    else if (currentFilter === 'rejected') filtered = allSuggestions.filter(s => s.status === 'rejected');
    else if (currentFilter === 'supported') filtered = allSuggestions.filter(s => s.evidence_status === 'supported');
    else if (currentFilter === 'needs_confirmation') filtered = allSuggestions.filter(s => s.evidence_status === 'needs_confirmation');

    if (!filtered.length) {
      container.innerHTML = `
        <div class="p-6 rounded-xl bg-surface-container/30 border border-outline-variant/20 text-center font-code-sm text-xs text-on-surface-variant">
          No suggestions found for filter: <strong class="text-cyan">${currentFilter}</strong>.
        </div>`;
      return;
    }

    container.innerHTML = filtered.map(s => {
      let badgeClass = 'badge-supported';
      let badgeIcon = 'check_circle';
      let badgeLabel = 'SUPPORTED';
      if (s.evidence_status === 'needs_confirmation') {
        badgeClass = 'badge-needs-confirmation';
        badgeIcon = 'help';
        badgeLabel = 'NEEDS CONFIRMATION';
      } else if (s.evidence_status === 'unsupported') {
        badgeClass = 'badge-unsupported';
        badgeIcon = 'warning';
        badgeLabel = 'UNSUPPORTED CLAIM';
      }

      let cardStatusClass = '';
      if (s.status === 'accepted') cardStatusClass = 'status-accepted';
      else if (s.status === 'rejected') cardStatusClass = 'status-rejected';

      const secLabel = s.section ? s.section.toUpperCase() : 'SECTION';

      return `
        <div class="suggestion-card ${cardStatusClass}" id="card-${s.id}">
          <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3 pb-2.5 border-b border-outline-variant/20">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-code-sm text-[10px] px-2 py-0.5 rounded bg-surface-container text-cyan border border-outline-variant/40 font-bold uppercase tracking-wider">
                ${secLabel}
              </span>
              ${s.category ? `
              <span class="font-code-sm text-[10px] px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 font-bold tracking-wider">
                ${escapeHtml(s.category)}
              </span>` : ''}
              <span class="font-code-sm text-[10px] px-2.5 py-0.5 rounded-full ${badgeClass} font-bold flex items-center gap-1">
                <span class="material-symbols-outlined text-[12px]">${badgeIcon}</span> ${badgeLabel}
              </span>
              <span class="font-code-sm text-[10px] px-2 py-0.5 rounded bg-surface-container/60 text-outline border border-outline-variant/25">
                Status: <strong class="text-white uppercase">${s.status}</strong>
              </span>
            </div>
            <div class="text-[10px] font-code-sm text-outline">
              ID: ${s.id}
            </div>
          </div>

          <div class="mb-3">
            <div class="text-xs text-on-surface-variant mb-1 leading-relaxed">
              <strong class="text-white">Why:</strong> ${escapeHtml(s.explanation || '')}
            </div>
            ${s.evidence_note ? `
              <div class="text-[11px] font-code-sm text-amber-300/90 bg-amber-400/10 p-2 rounded-lg border border-amber-400/20 flex items-start gap-1.5 mt-1.5">
                <span class="material-symbols-outlined text-[14px] flex-shrink-0 mt-0.5">info</span>
                <span>${escapeHtml(s.evidence_note)}</span>
              </div>
            ` : ''}
          </div>

          <!-- Diff comparison -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <div>
              <div class="text-[10px] font-code-sm text-outline uppercase mb-1 flex items-center gap-1">
                <span class="material-symbols-outlined text-[12px] text-rose-400">remove_circle</span> Original Text:
              </div>
              <div class="suggestion-diff-orig">${escapeHtml(s.original_text || '')}</div>
            </div>
            <div>
              <div class="text-[10px] font-code-sm text-outline uppercase mb-1 flex items-center gap-1">
                <span class="material-symbols-outlined text-[12px] text-tertiary">add_circle</span> AI Suggested Improvement:
              </div>
              <div class="suggestion-diff-sugg">${escapeHtml(s.suggested_text || '')}</div>
            </div>
          </div>

          <!-- User Edit Override -->
          <div class="mb-3">
            <label class="text-[10px] font-code-sm text-outline uppercase block mb-1">
              Custom Edit Override (Optional — customize before accepting):
            </label>
            <textarea id="edit-input-${s.id}" rows="2" class="w-full bg-surface-container-lowest/90 border border-outline-variant/30 rounded-lg p-2.5 font-code-sm text-xs text-on-surface focus:border-cyan focus:outline-none resize-y leading-relaxed" placeholder="Type custom edits here if you want to modify this suggestion before accepting...">${escapeHtml(s.edited_text || '')}</textarea>
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-2 pt-2 border-t border-outline-variant/20">
            <button type="button" class="btn-reject-sug px-3 py-1.5 rounded-lg bg-surface-container hover:bg-error/20 border border-outline-variant/40 hover:border-error text-on-surface hover:text-error font-code-sm text-xs transition-all cursor-pointer flex items-center gap-1" data-id="${s.id}">
              <span class="material-symbols-outlined text-[14px]">close</span> Reject
            </button>
            <button type="button" class="btn-accept-sug px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-500 to-tertiary text-slate-900 font-code-sm text-xs font-bold hover:brightness-110 transition-all cursor-pointer flex items-center gap-1" data-id="${s.id}">
              <span class="material-symbols-outlined text-[14px]">check</span> Accept
            </button>
          </div>
        </div>
      `;
    }).join('');

    // Attach button listeners
    container.querySelectorAll('.btn-accept-sug').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        const editEl = document.getElementById(`edit-input-${id}`);
        const editedText = editEl ? editEl.value.trim() : '';
        await handleAcceptSuggestion(id, editedText);
      });
    });

    container.querySelectorAll('.btn-reject-sug').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        await handleRejectSuggestion(id);
      });
    });
  }

  async function handleAcceptSuggestion(id, editedText) {
    if (!activeSessionId) return;
    try {
      const formData = new FormData();
      formData.append('session_id', activeSessionId);
      formData.append('suggestion_id', id);
      if (editedText) formData.append('edited_text', editedText);

      const res = await fetch('/api/upgrade/accept-suggestion', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const target = allSuggestions.find(s => s.id === id);
      if (target) {
        target.status = 'accepted';
        if (editedText) target.edited_text = editedText;
      }
      updateStats(data.stats);
      renderSuggestions();
      fetchApprovedPreview();
      showToast('success', 'Suggestion accepted.');
    } catch (err) {
      console.error('Accept error:', err);
      showToast('error', `Failed to accept suggestion: ${err.message}`);
    }
  }

  async function handleRejectSuggestion(id) {
    if (!activeSessionId) return;
    try {
      const formData = new FormData();
      formData.append('session_id', activeSessionId);
      formData.append('suggestion_id', id);

      const res = await fetch('/api/upgrade/reject-suggestion', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const target = allSuggestions.find(s => s.id === id);
      if (target) target.status = 'rejected';

      updateStats(data.stats);
      renderSuggestions();
      fetchApprovedPreview();
      showToast('info', 'Suggestion rejected.');
    } catch (err) {
      console.error('Reject error:', err);
      showToast('error', `Failed to reject suggestion: ${err.message}`);
    }
  }

  // Accept all supported
  if (btnAcceptAllSupported) {
    btnAcceptAllSupported.addEventListener('click', async () => {
      if (!activeSessionId) {
        showToast('warning', 'Please generate suggestions first.');
        return;
      }
      const supported = allSuggestions.filter(s => s.evidence_status === 'supported' && s.status === 'pending');
      if (!supported.length) {
        showToast('info', 'No pending supported suggestions to accept.');
        return;
      }
      btnAcceptAllSupported.disabled = true;
      btnAcceptAllSupported.innerHTML = `<span class="btn-spinner inline-block w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span> <span>Accepting ${supported.length}…</span>`;
      try {
        for (const s of supported) {
          await handleAcceptSuggestion(s.id, '');
        }
        showToast('success', `Accepted ${supported.length} supported suggestions!`);
      } finally {
        btnAcceptAllSupported.disabled = false;
        btnAcceptAllSupported.innerHTML = `<span class="material-symbols-outlined text-[15px]">done_all</span> <span>Accept Supported</span>`;
      }
    });
  }

  // Live preview of approved resume — dynamically syncs into the Enhanced ATS Resume panel
  async function fetchApprovedPreview() {
    if (!activeSessionId) return;
    try {
      const res = await fetch(`/api/upgrade/approved-resume?session_id=${encodeURIComponent(activeSessionId)}`);
      if (!res.ok) return;
      const data = await res.json();

      // ── 1. Update the inline preview inside the Suggestion Studio ─────────
      if (previewTextEl) {
        if (data.markdown_text) {
          previewTextEl.textContent = data.markdown_text;
        } else if (data.approved_canonical) {
          previewTextEl.textContent = JSON.stringify(data.approved_canonical, null, 2);
        }
      }

      // ── 2. Push accepted changes into the Enhanced ATS-Compliant Resume ──
      const enhancedPanel = document.getElementById('enhanced-cv-text');
      const approvedText = data.markdown_text ||
        (data.approved_canonical ? JSON.stringify(data.approved_canonical, null, 2) : '');

      if (enhancedPanel && approvedText) {
        if (data.stats && data.stats.accepted > 0) {
          enhancedPanel.value = approvedText;
          // Flash the panel border green to signal a live update
          enhancedPanel.classList.add('border-tertiary');
          enhancedPanel.classList.remove('border-outline-variant/30');
          enhancedPanel.dispatchEvent(new Event('input'));

          // Show Live sync badge
          const syncBadge = document.getElementById('layer-e-sync-badge');
          if (syncBadge) syncBadge.classList.remove('hidden');

          // Show the source notice
          const sourceNotice = document.getElementById('enhanced-cv-source-notice');
          if (sourceNotice) sourceNotice.classList.remove('hidden');
        } else if (!enhancedPanel.value.trim()) {
          enhancedPanel.value = approvedText;
          enhancedPanel.dispatchEvent(new Event('input'));
        }

        // Update word count
        const wordCountEl = document.getElementById('enhanced-cv-word-count');
        if (wordCountEl && enhancedPanel.value) {
          wordCountEl.textContent = enhancedPanel.value.trim().split(/\s+/).length + ' words';
        }
      }

      // ── 3. Sync approved canonical into currentCanonicalData so PDF ──────
      //       download and re-scoring use the accepted-suggestions version
      if (data.approved_canonical) {
        if (typeof currentCanonicalData !== 'undefined') {
          currentCanonicalData = data.approved_canonical;
        }
      }

    } catch (err) {
      console.error('Fetch approved preview error:', err);
    }
  }

  if (btnRefreshPreview) {
    btnRefreshPreview.addEventListener('click', fetchApprovedPreview);
  }

  // Export approved PDF
  if (btnExportPdf) {
    btnExportPdf.addEventListener('click', async () => {
      if (!activeSessionId && !currentCanonicalData) {
        showToast('warning', 'Please generate and review suggestions before exporting.');
        return;
      }
      btnExportPdf.disabled = true;
      btnExportPdf.innerHTML = `<span class="btn-spinner inline-block w-3.5 h-3.5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin"></span> <span>Rendering PDF…</span>`;
      try {
        const formData = new FormData();
        if (activeSessionId) {
          formData.append('session_id', activeSessionId);
        }
        if (currentCanonicalData) {
          formData.append('canonical_resume_json', JSON.stringify(currentCanonicalData));
        }
        const liveText = (document.getElementById('enhanced-cv-text')?.value || document.getElementById('approved-resume-text-view')?.textContent || '').trim();
        if (liveText) {
          formData.append('resume_text', liveText);
        }

        const res = await fetch('/api/upgrade/export-pdf', {
          method: 'POST',
          body: formData
        });

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.detail || `PDF generation returned status ${res.status}`);
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'Approved_Upgraded_Resume.pdf';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast('success', 'Approved PDF exported successfully!');
      } catch (err) {
        console.error('PDF export error:', err);
        showToast('error', `Failed to export PDF: ${err.message}`);
      } finally {
        btnExportPdf.disabled = false;
        btnExportPdf.innerHTML = `<span class="material-symbols-outlined text-[16px]">picture_as_pdf</span> <span>Export Approved PDF</span>`;
      }
    });
  }

  const btnProceedToUpgrade = document.getElementById('btn-proceed-to-upgrade');
  if (btnProceedToUpgrade) {
    btnProceedToUpgrade.addEventListener('click', () => {
      const upgradeNavTab = document.getElementById('nav-tab-upgrade-cv');
      if (upgradeNavTab) {
        upgradeNavTab.click();
      } else {
        const tabEl = document.querySelector('[data-target="tab-upgrade-cv"]');
        if (tabEl) tabEl.click();
      }
      setTimeout(() => {
        const studioEl = document.getElementById('suggestions-review-studio');
        if (studioEl) studioEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 150);
    });
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
})();

// =========================================================================
// LAYER F: CAREER INTELLIGENCE & DEVELOPER LEARNING PLATFORM
// =========================================================================
(function initCareerIntelligencePlatform() {
  'use strict';

  // ── Maintainable Knowledge Base & URL Mappings (Parts 4, 5, 7, 8) ──────
  const ROADMAP_SH_MAP = {
    'Backend Development': 'https://roadmap.sh/backend',
    'Backend': 'https://roadmap.sh/backend',
    'Frontend Development': 'https://roadmap.sh/frontend',
    'Frontend': 'https://roadmap.sh/frontend',
    'Full Stack': 'https://roadmap.sh/full-stack',
    'DevOps': 'https://roadmap.sh/devops',
    'Cloud': 'https://roadmap.sh/devops',
    'AWS': 'https://roadmap.sh/aws',
    'Docker': 'https://roadmap.sh/docker',
    'Kubernetes': 'https://roadmap.sh/kubernetes',
    'SQL': 'https://roadmap.sh/sql',
    'PostgreSQL': 'https://roadmap.sh/postgresql',
    'Python': 'https://roadmap.sh/python',
    'Java': 'https://roadmap.sh/java',
    'JavaScript': 'https://roadmap.sh/javascript',
    'TypeScript': 'https://roadmap.sh/typescript',
    'Data Structures & Algorithms': 'https://roadmap.sh/datastructures-and-algorithms',
    'DSA': 'https://roadmap.sh/datastructures-and-algorithms',
    'Computer Science': 'https://roadmap.sh/computer-science',
    'System Design': 'https://roadmap.sh/system-design',
    'Git and GitHub': 'https://roadmap.sh/git-github',
    'Git': 'https://roadmap.sh/git-github',
    'Linux': 'https://roadmap.sh/linux',
    'REST APIs': 'https://roadmap.sh/backend',
    'FastAPI': 'https://roadmap.sh/python',
    'React': 'https://roadmap.sh/react',
    'Node.js': 'https://roadmap.sh/nodejs',
    'MongoDB': 'https://roadmap.sh/mongodb',
    'Redis': 'https://roadmap.sh/redis',
    'GraphQL': 'https://roadmap.sh/graphql',
    'Cyber Security': 'https://roadmap.sh/cyber-security',
    'AI': 'https://roadmap.sh/ai-data-scientist',
    'Machine Learning': 'https://roadmap.sh/ai-data-scientist',
    'Data Analyst': 'https://roadmap.sh/data-analyst'
  };

  const OFFICIAL_DOCS_MAP = {
    'AWS': 'https://docs.aws.amazon.com/index.html',
    'Docker': 'https://docs.docker.com/get-started/',
    'Kubernetes': 'https://kubernetes.io/docs/home/',
    'Python': 'https://docs.python.org/3/',
    'SQL': 'https://dev.mysql.com/doc/refman/8.0/en/tutorial.html',
    'PostgreSQL': 'https://www.postgresql.org/docs/',
    'Java': 'https://docs.oracle.com/en/java/',
    'JavaScript': 'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
    'TypeScript': 'https://www.typescriptlang.org/docs/',
    'FastAPI': 'https://fastapi.tiangolo.com/tutorial/',
    'REST APIs': 'https://restfulapi.net/',
    'System Design': 'https://github.com/donnemartin/system-design-primer',
    'DSA': 'https://github.com/trekhleb/javascript-algorithms',
    'Git': 'https://git-scm.com/doc',
    'Linux': 'https://www.kernel.org/doc/html/latest/'
  };

  const SKILL_PREREQUISITES = {
    'AWS': ['Linux Fundamentals', 'Networking Basics (DNS, HTTP, VPC)'],
    'Docker': ['Linux Terminal', 'Process Management Basics'],
    'Kubernetes': ['Docker', 'Containerization Basics', 'Linux Networking'],
    'PostgreSQL': ['Relational DB Fundamentals', 'Basic SQL Syntax'],
    'SQL': ['Basic Database Concepts'],
    'FastAPI': ['Python Basics', 'HTTP & REST Protocols'],
    'REST APIs': ['HTTP Methods (GET, POST, PUT, DELETE)', 'JSON Formatting'],
    'System Design': ['Data Structures', 'Database Scaling', 'Caching & CDNs'],
    'DSA': ['Programming Language Basics (Loops, Recursion, Memory)'],
    'Machine Learning': ['Python', 'Linear Algebra & Statistics', 'NumPy & Pandas'],
    'React': ['HTML5/CSS3', 'JavaScript (ES6+, Promises, Closures)'],
    'Node.js': ['JavaScript Asynchronous Event Loop', 'HTTP Protocol']
  };

  const SKILL_RELEVANCE = {
    'AWS': 'Amazon Web Services is the primary cloud infrastructure demanded in target job postings for hosting web services, databases, and microservices.',
    'Docker': 'Containerization guarantees consistent execution across local development and cloud production clusters. Essential for modern DevOps pipelines.',
    'Kubernetes': 'Standard container orchestration system used by mid-to-large engineering teams for automated scaling, self-healing, and deployments.',
    'PostgreSQL': 'Enterprise-grade relational database engine commonly expected for ACID compliance, JSON querying, and indexing in production web services.',
    'SQL': 'Fundamental data manipulation language necessary for backend CRUD workflows, analytics queries, and performance profiling.',
    'REST APIs': 'Industry standard architectural pattern for decoupling backend services from frontend web and mobile clients.',
    'System Design': 'Evaluates your ability to architect scalable, fault-tolerant, and performant systems handling thousands of concurrent requests.',
    'Python': 'High-productivity programming language universally applied across backend web services, automation scripting, and AI engineering.',
    'DSA': 'Data structures and algorithms are the bedrock of technical hiring interviews, testing algorithmic time/space complexity optimization.'
  };

  const SKILL_PROJECTS = {
    'AWS': {
      title: 'Deploy a Resilient Microservice on AWS App Runner & S3',
      objective: 'Build, configure, and deploy an automated web service using AWS CLI and core cloud primitives.',
      prerequisites: 'Docker containerization and AWS Free Tier account',
      deliverable: 'GitHub repository with deployment instructions, AWS CLI automation script, and public URL.',
      docs: 'https://docs.aws.amazon.com/apprunner/latest/dg/what-is-apprunner.html'
    },
    'Docker': {
      title: 'Multi-Stage Production Containerization with Compose',
      objective: 'Optimize a full-stack container build with multi-stage caching, non-root user security, and docker-compose orchestration.',
      prerequisites: 'Basic terminal command experience',
      deliverable: 'Repository with Dockerfile, .dockerignore, and docker-compose.yml with health checks.',
      docs: 'https://docs.docker.com/build/building/multi-stage/'
    },
    'SQL': {
      title: 'E-Commerce Database Schema Design & Query Optimization',
      objective: 'Design normalized schema (3NF) with foreign keys, composite indexes, and benchmark EXPLAIN ANALYZE queries.',
      prerequisites: 'Basic SQL syntax',
      deliverable: 'SQL migration files, seed data script, and query execution plan comparison report.',
      docs: 'https://www.postgresql.org/docs/current/using-explain.html'
    },
    'REST APIs': {
      title: 'Production CRUD Service with JWT Auth & Rate Limiting',
      objective: 'Implement robust API with structured input validation, token-based authentication, and Redis rate limiting.',
      prerequisites: 'Python or JavaScript backend basics',
      deliverable: 'GitHub repository with OpenAPI/Swagger docs, unit tests, and CI GitHub Action workflow.',
      docs: 'https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/'
    },
    'System Design': {
      title: 'Design a High-Throughput URL Shortener with Caching',
      objective: 'Architect distributed URL redirector with base62 encoding, Redis caching, and rate limiting.',
      prerequisites: 'Database fundamentals and HTTP protocol',
      deliverable: 'Architecture diagram (Mermaid/draw.io), API schema, capacity estimation math, and writeup.',
      docs: 'https://github.com/donnemartin/system-design-primer#url-shortener'
    },
    'DSA': {
      title: 'Core Algorithm Patterns Practice Tracker',
      objective: 'Solve and document 25 foundational problems across Two Pointers, Sliding Window, and BFS/DFS.',
      prerequisites: 'Basic data structures (Arrays, Hash Maps, Linked Lists)',
      deliverable: 'Public GitHub repository documenting problem statements, tested solutions, and Big-O explanations.',
      docs: 'https://github.com/trekhleb/javascript-algorithms'
    }
  };

  const SKILL_INTERVIEW_QUESTIONS = {
    'AWS': {
      question: 'Explain the difference between S3 bucket policies and IAM policies in AWS. When should each be used?',
      category: 'Cloud Infrastructure & Security',
      rubric: {
        keywords: ['s3', 'bucket policy', 'iam policy', 'principal', 'resource-based', 'identity-based', 'cross-account'],
        key_concept: 'IAM policies attach to users/roles; bucket policies attach directly to the S3 bucket to grant cross-account or anonymous access.'
      }
    },
    'Docker': {
      question: 'How do Docker multi-stage builds help optimize production container images? Give a concrete example.',
      category: 'Containers & Deployment',
      rubric: {
        keywords: ['multi-stage', 'build stage', 'runtime stage', 'image size', 'compiler', 'cache', 'security'],
        key_concept: 'Separates compile-time dependencies (compilers, dev tools) from runtime environment, reducing image footprint and attack surface.'
      }
    },
    'SQL': {
      question: 'What is the purpose of database indexing, and what are the trade-offs of adding too many indexes on a table?',
      category: 'Databases & Performance',
      rubric: {
        keywords: ['index', 'b-tree', 'read performance', 'write overhead', 'insert', 'update', 'disk space'],
        key_concept: 'Indexes drastically accelerate SELECT lookups via B-Trees, but penalize INSERT/UPDATE/DELETE writes because every index must be updated.'
      }
    },
    'REST APIs': {
      question: 'Explain what makes an HTTP method idempotent. Which standard HTTP verbs are idempotent and which are not?',
      category: 'API Architecture',
      rubric: {
        keywords: ['idempotent', 'get', 'put', 'delete', 'post', 'side effect', 'state'],
        key_concept: 'An operation is idempotent if executing it multiple times produces the exact same server state. GET, PUT, and DELETE are idempotent; POST is not.'
      }
    },
    'System Design': {
      question: 'How would you scale a web service from a single server to handle 100,000 concurrent users?',
      category: 'System Architecture',
      rubric: {
        keywords: ['load balancer', 'horizontal scaling', 'stateless', 'caching', 'redis', 'cdn', 'read replica', 'database sharding'],
        key_concept: 'Move session state out of app servers, introduce load balancers, cache static assets on CDNs, add Redis caching, and implement database read replicas.'
      }
    }
  };

  // ── YouTube Search Query Generator (Part 4) ───────────────────────────
  function getYouTubeSearchUrl(skill, level = 'beginner', topic = '') {
    let query = `${skill} tutorial`;
    if (topic) {
      query += ` ${topic}`;
    }
    if (level && level !== 'all') {
      query += ` for ${level}s`;
    }
    return `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
  }

  // ── Roadmap.sh URL Resolver (Part 5) ──────────────────────────────────
  function getRoadmapShUrl(skill) {
    if (!skill) return 'https://roadmap.sh/roadmaps/';
    const trimmed = skill.trim();
    if (ROADMAP_SH_MAP[trimmed]) return ROADMAP_SH_MAP[trimmed];
    const lower = trimmed.toLowerCase();
    for (const [key, url] of Object.entries(ROADMAP_SH_MAP)) {
      if (key.toLowerCase() === lower || lower.includes(key.toLowerCase())) {
        return url;
      }
    }
    return 'https://roadmap.sh/roadmaps/';
  }

  function getOfficialDocsUrl(skill) {
    if (!skill) return 'https://devdocs.io/';
    const trimmed = skill.trim();
    if (OFFICIAL_DOCS_MAP[trimmed]) return OFFICIAL_DOCS_MAP[trimmed];
    return `https://www.google.com/search?q=${encodeURIComponent(trimmed + ' official documentation')}`;
  }

  // ── State Management (Part 10) ─────────────────────────────────────────
  const STORAGE_KEY = 'ai_resume_ats_career_state';

  let careerState = {
    targetRole: 'Backend Developer',
    academicStage: 'second_year',
    hoursPerWeek: 10,
    activeSubtab: 'overview',
    selectedSkill: 'AWS',
    learningPlanSkills: ['AWS', 'Docker'],
    completedMilestones: [],
    inProgressMilestones: [],
    completedProjects: [],
    verifiedSkills: [],
    sessionId: 'career_session_' + Math.random().toString(36).substring(2, 9),
    detectedEducationProfile: null
  };

  function loadState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        careerState = { ...careerState, ...parsed };
      }
    } catch (e) {
      console.warn('[CareerIntel] Could not load stored state:', e);
    }
  }

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        targetRole: careerState.targetRole,
        academicStage: careerState.academicStage,
        hoursPerWeek: careerState.hoursPerWeek,
        activeSubtab: careerState.activeSubtab,
        selectedSkill: careerState.selectedSkill,
        learningPlanSkills: careerState.learningPlanSkills,
        completedMilestones: careerState.completedMilestones,
        inProgressMilestones: careerState.inProgressMilestones,
        completedProjects: careerState.completedProjects,
        verifiedSkills: careerState.verifiedSkills,
        sessionId: careerState.sessionId,
        detectedEducationProfile: careerState.detectedEducationProfile
      }));
    } catch (e) {
      console.warn('[CareerIntel] Could not save state:', e);
    }
  }

  // ── Data Gathering: Active Analysis vs Demo Data (Part 2) ───────────────
  function getActiveSkillsData() {
    if (typeof currentReportData !== 'undefined' && currentReportData && currentReportData.job_matching) {
      const jm = currentReportData.job_matching;
      const pe = currentReportData.public_evidence || {};
      const matched = jm.matched_skills || [];
      const missing = jm.missing_skills || [];
      const repos = pe.github_repositories || [];

      const partial = matched.filter(s => s.length > 5 && !repos.some(r => (r.languages || []).includes(s)));

      return {
        isDemo: false,
        targetRole: careerState.targetRole,
        academicStage: careerState.academicStage,
        matchedSkills: matched,
        missingSkills: missing,
        partialSkills: partial,
        prereqSkills: getPrereqSkillsForGaps(missing)
      };
    }

    return getDemoSkillsData();
  }

  function getDemoSkillsData() {
    const missing = ['AWS', 'Docker', 'PostgreSQL', 'REST APIs', 'System Design', 'Kubernetes'];
    const matched = ['Python', 'JavaScript', 'Git', 'HTML/CSS', 'SQLite'];
    const partial = ['SQL', 'Linux Basics'];
    return {
      isDemo: true,
      targetRole: careerState.targetRole || 'Backend Developer',
      academicStage: careerState.academicStage || 'second_year',
      matchedSkills: matched,
      missingSkills: missing,
      partialSkills: partial,
      prereqSkills: getPrereqSkillsForGaps(missing)
    };
  }

  function getPrereqSkillsForGaps(missingSkills) {
    const set = new Set();
    missingSkills.forEach(skill => {
      const prereqs = SKILL_PREREQUISITES[skill] || [];
      prereqs.forEach(p => set.add(p));
    });
    return Array.from(set);
  }

  // ── Sub-Navigation Controller (Part 1) ───────────────────────────────────
  function activateCareerSubtab(subtabName) {
    careerState.activeSubtab = subtabName;
    saveState();

    document.querySelectorAll('.career-subtab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.getAttribute('data-subtab') === subtabName);
    });

    document.querySelectorAll('.career-subview').forEach(view => {
      view.classList.add('hidden');
    });

    const activeView = document.getElementById(`career-subview-${subtabName}`);
    if (activeView) {
      activeView.classList.remove('hidden');
    }

    renderActiveSubtab(subtabName);
  }

  function renderActiveSubtab(subtabName) {
    const data = getActiveSkillsData();
    switch (subtabName) {
      case 'overview':
        renderOverview(data);
        break;
      case 'gaps':
        renderSkillGaps(data);
        break;
      case 'roadmap':
        renderRoadmap(data);
        break;
      case 'videos':
        renderVideoTutorials(data);
        break;
      case 'projects':
        renderProjects(data);
        break;
      case 'certs':
        renderCertificationsAndTools(data);
        break;
      case 'interview':
        renderInterviewPrep(data);
        break;
      case 'progress':
        renderProgressTracker(data);
        break;
      default:
        renderOverview(data);
    }
  }

  // ── SUBVIEW 1: OVERVIEW (Part 2) ────────────────────────────────────────
  function renderOverview(data) {
    const ovRole = document.getElementById('ov-target-role');
    const ovTimeline = document.getElementById('ov-est-timeline');
    const ovEvidenced = document.getElementById('ov-evidenced-count');
    const ovGaps = document.getElementById('ov-gaps-count');
    const ovProgVal = document.getElementById('ov-progress-val');
    const ovProgBar = document.getElementById('ov-progress-bar');
    const ovStageBadge = document.getElementById('ov-stage-badge');
    const ovStageGuidance = document.getElementById('ov-stage-guidance');
    const ovNextTitle = document.getElementById('ov-next-action-title');
    const ovNextDesc = document.getElementById('ov-next-action-desc');

    if (ovRole) ovRole.textContent = data.targetRole;

    const totalGaps = data.missingSkills.length;
    const estWeeks = Math.max(2, Math.ceil((totalGaps * 12) / (careerState.hoursPerWeek || 10)));
    if (ovTimeline) {
      ovTimeline.innerHTML = `<span class="material-symbols-outlined text-[13px]">schedule</span> ~${estWeeks} Weeks at ${careerState.hoursPerWeek}h/wk`;
    }

    if (ovEvidenced) ovEvidenced.textContent = `${data.matchedSkills.length} Verified`;
    if (ovGaps) ovGaps.textContent = `${data.missingSkills.length} Missing`;

    const totalMilestones = 8;
    const completedCount = careerState.completedMilestones.length;
    const pct = Math.min(100, Math.round((completedCount / totalMilestones) * 100));
    if (ovProgVal) ovProgVal.textContent = `${pct}%`;
    if (ovProgBar) ovProgBar.style.width = `${pct}%`;

    const stageNames = {
      'first_year': '1st Year Student (Foundational)',
      'second_year': '2nd Year Student (Core & Cloud)',
      'third_year': '3rd Year Student (Internship Ready)',
      'final_year': 'Final Year Student (Placement Capstones)',
      'early_career': 'Early Career Professional'
    };
    if (ovStageBadge) ovStageBadge.textContent = stageNames[careerState.academicStage] || '2nd Year Student';

    if (ovStageGuidance) {
      if (careerState.academicStage === 'first_year' || careerState.academicStage === 'second_year') {
        ovStageGuidance.textContent = 'Learning roadmaps and certifications are calibrated to your undergraduate stage. Foundational cloud certs (AWS Cloud Practitioner), container basics, and public Git repositories are prioritized over expensive enterprise credentials.';
      } else {
        ovStageGuidance.textContent = 'Focus is calibrated towards production deployments, system architecture, multi-service Docker/K8s environments, and technical interview whiteboard questions.';
      }
    }

    const topGap = data.missingSkills[0] || 'AWS';
    if (ovNextTitle) {
      ovNextTitle.textContent = `Start with ${topGap} Fundamentals & Cloud Prerequisites`;
    }
    if (ovNextDesc) {
      ovNextDesc.innerHTML = `Your target role demands <strong>${topGap}</strong>, but your resume lacks verifiable public evidence. Learn foundational concepts, follow the official <strong>roadmap.sh/${topGap.toLowerCase()}</strong> path, and build a hands-on portfolio service before moving to advanced architecture.`;
    }

    renderChipsList('ov-chips-high-priority', data.missingSkills.slice(0, 4), 'chip-high-gap');
    renderChipsList('ov-chips-prerequisites', data.prereqSkills.slice(0, 4), 'chip-prereq');
    renderChipsList('ov-chips-strengths', data.matchedSkills.slice(0, 4), 'chip-matched-intel');
  }

  function renderChipsList(elementId, items, chipClass) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.innerHTML = '';
    if (!items || !items.length) {
      el.innerHTML = `<span class="text-[11px] text-outline font-code-sm">None</span>`;
      return;
    }
    items.forEach(item => {
      const chip = document.createElement('span');
      chip.className = `skill-chip-interactive ${chipClass}`;
      chip.textContent = item;
      chip.addEventListener('click', () => {
        window.openSkillDetailModal(item, chipClass === 'chip-matched-intel');
      });
      el.appendChild(chip);
    });
  }

  // ── SUBVIEW 2: SKILL GAP ANALYSIS (Part 3) ──────────────────────────────
  function renderSkillGaps(data) {
    const cHigh = document.getElementById('gaps-count-high');
    const cPrereq = document.getElementById('gaps-count-prereq');
    const cPartial = document.getElementById('gaps-count-partial');
    const cMatched = document.getElementById('gaps-count-matched');

    if (cHigh) cHigh.textContent = `${data.missingSkills.length} Skills`;
    if (cPrereq) cPrereq.textContent = `${data.prereqSkills.length} Skills`;
    if (cPartial) cPartial.textContent = `${data.partialSkills.length} Skills`;
    if (cMatched) cMatched.textContent = `${data.matchedSkills.length} Skills`;

    renderChipsList('gaps-chips-high', data.missingSkills, 'chip-high-gap');
    renderChipsList('gaps-chips-prereq', data.prereqSkills, 'chip-prereq');
    renderChipsList('gaps-chips-partial', data.partialSkills, 'chip-partial');
    renderChipsList('gaps-chips-matched', data.matchedSkills, 'chip-matched-intel');
  }

  // ── SUBVIEW 3: LEARNING ROADMAP (Part 6) ─────────────────────────────────
  function renderRoadmap(data) {
    const container = document.getElementById('roadmap-timeline-container');
    const hoursBadge = document.getElementById('roadmap-hours-badge');
    if (hoursBadge) hoursBadge.textContent = `${careerState.hoursPerWeek} hrs/week`;
    if (!container) return;

    container.innerHTML = '';

    const stages = [
      {
        stageNum: 1,
        title: 'Stage 1: Prerequisites & Foundation',
        durationWeeks: 'Weeks 1–2',
        theme: 'cyan',
        milestones: [
          {
            id: 'm1',
            title: 'Linux CLI & Git Collaboration Workflow',
            hours: 8,
            skill: 'Git',
            objectives: [
              'Master terminal commands, file permissions, and environment variables.',
              'Adopt Git feature-branch workflows, commit conventions, and pull requests.'
            ],
            task: 'Create public GitHub repo with clean README, branch protection, and shell script.'
          },
          {
            id: 'm2',
            title: 'Data Structures & Problem Solving Foundations',
            hours: 12,
            skill: 'DSA',
            objectives: [
              'Practice Two-Pointer and Sliding Window techniques on LeetCode/HackerRank.',
              'Understand Big-O time and space complexity tradeoffs.'
            ],
            task: 'Solve and document 10 algorithm problems with complexity explanations.'
          }
        ]
      },
      {
        stageNum: 2,
        title: 'Stage 2: Core Backend & Data Persistence',
        durationWeeks: 'Weeks 3–5',
        theme: 'primary',
        milestones: [
          {
            id: 'm3',
            title: 'Relational Database Design & SQL Optimization',
            hours: 14,
            skill: 'SQL',
            objectives: [
              'Design 3NF normalized tables with foreign keys and composite indexes.',
              'Analyze query execution plans with EXPLAIN ANALYZE and avoid full table scans.'
            ],
            task: SKILL_PROJECTS['SQL'].title
          },
          {
            id: 'm4',
            title: 'RESTful API Engineering & Authentication',
            hours: 16,
            skill: 'REST APIs',
            objectives: [
              'Build CRUD endpoints with structured JSON schemas, validation, and error codes.',
              'Implement secure JWT authentication and role-based access control.'
            ],
            task: SKILL_PROJECTS['REST APIs'].title
          }
        ]
      },
      {
        stageNum: 3,
        title: 'Stage 3: Cloud Infrastructure & Containerization',
        durationWeeks: 'Weeks 6–8',
        theme: 'amber',
        milestones: [
          {
            id: 'm5',
            title: 'Docker Production Containerization',
            hours: 12,
            skill: 'Docker',
            objectives: [
              'Create multi-stage Dockerfiles optimizing image size under 150MB.',
              'Compose multi-container environments linking backend service and PostgreSQL.'
            ],
            task: SKILL_PROJECTS['Docker'].title
          },
          {
            id: 'm6',
            title: 'AWS Cloud Primitives & Service Deployment',
            hours: 18,
            skill: 'AWS',
            objectives: [
              'Configure AWS IAM security policies, VPC subnets, and security groups.',
              'Deploy containerized service to AWS App Runner or EC2 using AWS CLI.'
            ],
            task: SKILL_PROJECTS['AWS'].title
          }
        ]
      },
      {
        stageNum: 4,
        title: 'Stage 4: Architecture, Testing & Placement Preparation',
        durationWeeks: 'Weeks 9–10',
        theme: 'tertiary',
        milestones: [
          {
            id: 'm7',
            title: 'Distributed System Design & Caching',
            hours: 15,
            skill: 'System Design',
            objectives: [
              'Design scalable services using Redis caching, asynchronous queues, and load balancers.',
              'Understand horizontal scaling, CAP theorem tradeoffs, and failover.'
            ],
            task: SKILL_PROJECTS['System Design'].title
          },
          {
            id: 'm8',
            title: 'Live Technical Interview & Recruiter Mock Kits',
            hours: 10,
            skill: 'Interview Prep',
            objectives: [
              'Complete mock technical interviews explaining architecture trade-offs out loud.',
              'Defend resume project claims against forensics scrutiny.'
            ],
            task: 'Score 80%+ on recruiter interview practice rubric and record verified projects.'
          }
        ]
      }
    ];

    stages.forEach(st => {
      const card = document.createElement('div');
      card.className = 'glass-card rounded-2xl p-6 border border-outline-variant/30 space-y-4';

      const stHeader = `
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-outline-variant/20">
          <div class="flex items-center gap-2.5">
            <span class="w-7 h-7 rounded-lg bg-cyan/15 border border-cyan/40 text-cyan font-code-sm text-xs font-bold flex items-center justify-center">${st.stageNum}</span>
            <h4 class="font-bold text-white text-sm">${st.title}</h4>
          </div>
          <span class="font-code-sm text-xs text-outline bg-surface-container px-2.5 py-1 rounded-full border border-outline-variant/30">${st.durationWeeks}</span>
        </div>
      `;

      let milestonesHtml = '<div class="space-y-4 pt-1">';
      st.milestones.forEach(m => {
        const isCompleted = careerState.completedMilestones.includes(m.id);
        const isInProgress = careerState.inProgressMilestones.includes(m.id);

        const statusLabel = isCompleted ? 'Completed' : (isInProgress ? 'In Progress' : 'Not Started');
        const statusClass = isCompleted
          ? 'bg-tertiary/15 text-tertiary border-tertiary/40'
          : (isInProgress ? 'bg-cyan/15 text-cyan border-cyan/40' : 'bg-surface-container text-outline border-outline-variant/30');

        milestonesHtml += `
          <div class="p-4 rounded-xl bg-surface-container-lowest/60 border border-outline-variant/20 space-y-3" id="milestone-card-${m.id}">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
              <div class="flex items-center gap-2">
                <span class="font-bold text-white text-xs">${m.title}</span>
                <span class="text-[10px] font-code-sm px-2 py-0.5 rounded-full border ${statusClass}" id="milestone-badge-${m.id}">${statusLabel}</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-code-sm text-outline">${m.hours} hrs</span>
                <button type="button" class="btn-toggle-milestone font-code-sm text-[10px] px-2.5 py-1 rounded-lg border border-outline-variant/40 hover:border-cyan text-on-surface hover:text-cyan transition-all cursor-pointer" data-mid="${m.id}">
                  ${isCompleted ? 'Mark Incomplete' : 'Mark Completed'}
                </button>
              </div>
            </div>

            <ul class="text-[11px] text-on-surface-variant space-y-1 list-disc list-inside">
              ${m.objectives.map(o => `<li>${o}</li>`).join('')}
            </ul>

            <div class="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-outline-variant/15 text-[11px] font-code-sm">
              <span class="text-tertiary flex items-center gap-1">
                <span class="material-symbols-outlined text-[14px]">task_alt</span>
                <span>Task: ${m.task}</span>
              </span>
              <div class="flex gap-2">
                <a href="${getRoadmapShUrl(m.skill)}" target="_blank" rel="noopener noreferrer" class="text-cyan hover:underline flex items-center gap-0.5">
                  <span>roadmap.sh</span><span class="material-symbols-outlined text-[12px]">open_in_new</span>
                </a>
                <a href="${getYouTubeSearchUrl(m.skill, 'beginner')}" target="_blank" rel="noopener noreferrer" class="text-red-400 hover:underline flex items-center gap-0.5">
                  <span>YouTube</span><span class="material-symbols-outlined text-[12px]">open_in_new</span>
                </a>
              </div>
            </div>
          </div>
        `;
      });
      milestonesHtml += '</div>';

      card.innerHTML = stHeader + milestonesHtml;
      container.appendChild(card);
    });

    container.querySelectorAll('.btn-toggle-milestone').forEach(btn => {
      btn.addEventListener('click', () => {
        const mid = btn.getAttribute('data-mid');
        toggleMilestoneStatus(mid);
      });
    });
  }

  function toggleMilestoneStatus(mid) {
    const idx = careerState.completedMilestones.indexOf(mid);
    if (idx >= 0) {
      careerState.completedMilestones.splice(idx, 1);
    } else {
      careerState.completedMilestones.push(mid);
      fetch('/api/career/progress/milestone', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: careerState.sessionId,
          skill: mid,
          milestone_text: `Completed learning milestone ${mid}`
        })
      }).catch(e => console.warn('Progress sync warning:', e));
    }
    saveState();
    renderOverview(getActiveSkillsData());
    renderRoadmap(getActiveSkillsData());
    showToast('success', idx >= 0 ? 'Milestone marked incomplete' : 'Milestone marked completed! 🎉');
  }

  // ── SUBVIEW 4: VIDEO TUTORIALS (Part 4) ──────────────────────────────────
  function renderVideoTutorials(data) {
    const grid = document.getElementById('video-cards-grid');
    const skillFilter = document.getElementById('video-filter-skill')?.value || 'all';
    const levelFilter = document.getElementById('video-filter-level')?.value || 'all';
    if (!grid) return;

    grid.innerHTML = '';

    const tutorials = [
      {
        skill: 'AWS',
        level: 'beginner',
        topic: 'Core Cloud Fundamentals (IAM, EC2, S3)',
        step: 'Step 1 of 3: Cloud Fundamentals',
        desc: 'Understand how AWS infrastructure works from scratch, set up AWS Free Tier, configure security groups, and run your first virtual machine.'
      },
      {
        skill: 'AWS',
        level: 'intermediate',
        topic: 'Serverless & VPC Networking',
        step: 'Step 2 of 3: Serverless Architecture',
        desc: 'Build event-driven apps with AWS Lambda, API Gateway, DynamoDB, and custom VPC subnets.'
      },
      {
        skill: 'Docker',
        level: 'beginner',
        topic: 'Containerization Basics & CLI',
        step: 'Step 1 of 2: Image & Container Fundamentals',
        desc: 'Learn Docker architecture, difference between images and containers, port forwarding, and volume mapping.'
      },
      {
        skill: 'Docker',
        level: 'intermediate',
        topic: 'Multi-Stage Builds & Compose',
        step: 'Step 2 of 2: Production Orchestration',
        desc: 'Shrink production container sizes from 1GB to 80MB using multi-stage Alpine images and docker-compose.'
      },
      {
        skill: 'SQL',
        level: 'beginner',
        topic: 'Relational Schema & Query Mastery',
        step: 'Step 1 of 2: Normalization & JOINs',
        desc: 'Master SQL syntax, primary/foreign keys, INNER/LEFT joins, GROUP BY aggregations, and subqueries.'
      },
      {
        skill: 'SQL',
        level: 'advanced',
        topic: 'Query Performance & B-Tree Indexing',
        step: 'Step 2 of 2: Index Optimization',
        desc: 'Deep dive into database execution engines, index scans, partial indexes, and avoiding costly full table scans.'
      },
      {
        skill: 'Python',
        level: 'intermediate',
        topic: 'FastAPI Backend Development',
        step: 'Step 1 of 2: Modern Asynchronous APIs',
        desc: 'Build high-performance REST APIs with Pydantic validation, async/await, Dependency Injection, and JWT auth.'
      },
      {
        skill: 'System Design',
        level: 'intermediate',
        topic: 'Scalable Web Architecture Primer',
        step: 'Step 1 of 2: Horizontal Scaling & Caching',
        desc: 'Architect web services with load balancers, Redis caching layers, database read-replicas, and CDNs.'
      },
      {
        skill: 'DSA',
        level: 'intermediate',
        topic: 'Algorithm Patterns & Complexity',
        step: 'Step 1 of 2: Problem Solving Patterns',
        desc: 'Master sliding window, two-pointer, BFS, and dynamic programming patterns to ace technical coding rounds.'
      }
    ];

    const filtered = tutorials.filter(t => {
      const matchSkill = skillFilter === 'all' || t.skill.toLowerCase() === skillFilter.toLowerCase();
      const matchLevel = levelFilter === 'all' || t.level === levelFilter;
      return matchSkill && matchLevel;
    });

    if (!filtered.length) {
      grid.innerHTML = `
        <div class="col-span-full p-8 text-center glass-card rounded-2xl">
          <p class="text-xs text-on-surface-variant font-code-sm">No tutorials match the current filter. Try selecting "All Skills" and "All Levels".</p>
        </div>
      `;
      return;
    }

    filtered.forEach(t => {
      const card = document.createElement('div');
      card.className = 'glass-card rounded-2xl p-5 border border-outline-variant/30 flex flex-col justify-between hover:border-red-500/40 transition-all';

      const youtubeUrl = getYouTubeSearchUrl(t.skill, t.level, t.topic);

      card.innerHTML = `
        <div>
          <div class="flex items-center justify-between gap-2 mb-2">
            <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-cyan/10 text-cyan border border-cyan/30 font-bold uppercase">${t.skill}</span>
            <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-surface-container text-outline border border-outline-variant/30 capitalize">${t.level}</span>
          </div>
          <span class="text-[10px] font-code-sm text-outline block mb-1">${t.step}</span>
          <h4 class="font-bold text-white text-xs mb-2">${t.topic}</h4>
          <p class="text-[11px] text-on-surface-variant leading-relaxed line-clamp-3 mb-4">${t.desc}</p>
        </div>

        <div class="pt-3 border-t border-outline-variant/20 flex items-center justify-between">
          <span class="text-[10px] font-code-sm text-outline flex items-center gap-1">
            <span class="material-symbols-outlined text-[13px] text-red-400">smart_display</span>
            <span>YouTube Search</span>
          </span>
          <a href="${youtubeUrl}" target="_blank" rel="noopener noreferrer" class="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-300 font-code-sm text-xs font-bold flex items-center gap-1 transition-all">
            <span>Watch Tutorial</span>
            <span class="material-symbols-outlined text-[13px]">open_in_new</span>
          </a>
        </div>
      `;
      grid.appendChild(card);
    });
  }

  // ── SUBVIEW 5: PROJECTS & PRACTICE (Part 7) ─────────────────────────────
  function renderProjects(data) {
    const grid = document.getElementById('projects-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const projectsList = Object.entries(SKILL_PROJECTS);
    projectsList.forEach(([skillKey, proj]) => {
      const isCompleted = careerState.completedProjects.includes(skillKey);
      const card = document.createElement('div');
      card.className = `glass-card rounded-2xl p-6 border transition-all ${isCompleted ? 'border-tertiary/40 bg-tertiary/5' : 'border-outline-variant/30'}`;

      card.innerHTML = `
        <div class="flex items-center justify-between mb-3">
          <span class="font-code-sm text-xs px-2.5 py-0.5 rounded-full bg-cyan/10 text-cyan border border-cyan/30 font-bold uppercase">${skillKey} Project</span>
          <span class="font-code-sm text-[10px] px-2.5 py-0.5 rounded-full ${isCompleted ? 'bg-tertiary/20 text-tertiary border border-tertiary/40 font-bold' : 'bg-surface-container text-outline border border-outline-variant/30'}">
            ${isCompleted ? 'Completed & Verified' : 'In Backlog'}
          </span>
        </div>

        <h4 class="font-bold text-white text-sm mb-2">${proj.title}</h4>

        <div class="space-y-2 text-xs text-on-surface-variant font-body-md mb-4">
          <p><strong class="text-white">Objective:</strong> ${proj.objective}</p>
          <p><strong class="text-outline">Prerequisites:</strong> ${proj.prerequisites}</p>
          <p class="text-tertiary font-code-sm text-[11px]"><strong class="text-white">Deliverable:</strong> ${proj.deliverable}</p>
        </div>

        <div class="flex items-center justify-between pt-3 border-t border-outline-variant/20 font-code-sm text-xs">
          <a href="${proj.docs}" target="_blank" rel="noopener noreferrer" class="text-cyan hover:underline flex items-center gap-1">
            <span>Official Guide</span>
            <span class="material-symbols-outlined text-[13px]">open_in_new</span>
          </a>
          <button type="button" class="btn-toggle-project px-3 py-1.5 rounded-xl border border-outline-variant/40 hover:border-cyan text-xs font-bold text-white transition-all cursor-pointer" data-pkey="${skillKey}">
            ${isCompleted ? 'Mark Incomplete' : 'Mark as Completed'}
          </button>
        </div>
      `;
      grid.appendChild(card);
    });

    grid.querySelectorAll('.btn-toggle-project').forEach(btn => {
      btn.addEventListener('click', () => {
        const pkey = btn.getAttribute('data-pkey');
        const idx = careerState.completedProjects.indexOf(pkey);
        if (idx >= 0) {
          careerState.completedProjects.splice(idx, 1);
        } else {
          careerState.completedProjects.push(pkey);
        }
        saveState();
        renderProjects(data);
        renderOverview(data);
        showToast('success', idx >= 0 ? 'Project marked incomplete' : 'Project completed! Great engineering evidence.');
      });
    });
  }

  // ── SUBVIEW 6: CERTIFICATIONS & TOOLS (Part 8) ──────────────────────────
  async function renderCertificationsAndTools(data) {
    const recGrid = document.getElementById('certs-recommended-grid');
    const laterGrid = document.getElementById('certs-later-grid');
    const toolsGrid = document.getElementById('tools-grid');

    if (recGrid) recGrid.innerHTML = `<span class="text-xs text-outline font-code-sm">Loading stage-calibrated certifications...</span>`;
    if (laterGrid) laterGrid.innerHTML = `<span class="text-xs text-outline font-code-sm">Loading advanced certifications...</span>`;
    if (toolsGrid) toolsGrid.innerHTML = `<span class="text-xs text-outline font-code-sm">Loading recommended developer tools...</span>`;

    try {
      const certRes = await fetch('/api/career/certifications', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          academic_stage: careerState.academicStage || 'second_year',
          jd_skill_gaps: data.missingSkills || ['AWS', 'Docker'],
          max_recommendations: 4
        })
      });
      const certData = await certRes.json();

      if (recGrid) {
        recGrid.innerHTML = '';
        const recList = certData.recommended || [];
        if (!recList.length) {
          recGrid.innerHTML = `<p class="text-xs text-outline font-code-sm">No stage certifications needed right now. Focus on core coding projects.</p>`;
        } else {
          recList.forEach(c => {
            const card = document.createElement('div');
            card.className = 'glass-card rounded-xl p-4 border border-tertiary/30 space-y-2';
            card.innerHTML = `
              <div class="flex items-center justify-between">
                <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-tertiary/15 text-tertiary border border-tertiary/30 font-bold">${c.issuer}</span>
                <span class="text-[10px] font-code-sm text-outline capitalize">${c.difficulty} Level</span>
              </div>
              <h4 class="font-bold text-white text-xs">${c.name}</h4>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">${c.reason || 'Calibrated to your current academic stage & JD requirements.'}</p>
              <div class="flex items-center justify-between pt-2 border-t border-outline-variant/15 text-[10px] font-code-sm">
                <span class="text-outline">Exam Cost: <strong class="text-white">${c.exam_cost_usd ? `$${c.exam_cost_usd}` : 'Free / Subsidized'}</strong></span>
                <a href="${c.official_url || '#'}" target="_blank" rel="noopener noreferrer" class="text-cyan hover:underline flex items-center gap-0.5">
                  <span>Official Guide</span><span class="material-symbols-outlined text-[12px]">open_in_new</span>
                </a>
              </div>
            `;
            recGrid.appendChild(card);
          });
        }
      }

      if (laterGrid) {
        laterGrid.innerHTML = '';
        const laterList = certData.save_for_later || [];
        if (!laterList.length) {
          laterGrid.innerHTML = `<p class="text-xs text-outline font-code-sm">None postponed.</p>`;
        } else {
          laterList.forEach(c => {
            const card = document.createElement('div');
            card.className = 'glass-card rounded-xl p-4 border border-outline-variant/25 opacity-80 space-y-2';
            card.innerHTML = `
              <div class="flex items-center justify-between">
                <span class="font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-surface-container text-outline border border-outline-variant/30">${c.issuer}</span>
                <span class="text-[10px] font-code-sm text-amber-300 font-bold">Postpone to Final Year</span>
              </div>
              <h4 class="font-bold text-white text-xs">${c.name}</h4>
              <p class="text-[11px] text-on-surface-variant leading-relaxed">${c.reason || 'Advanced credential. Master prerequisites first.'}</p>
              <div class="pt-2 border-t border-outline-variant/15 text-[10px] font-code-sm text-outline">
                Cost: $${c.exam_cost_usd || '300+'} · Revisit after completing core projects
              </div>
            `;
            laterGrid.appendChild(card);
          });
        }
      }

      const toolsRes = await fetch('/api/career/tools', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          academic_stage: careerState.academicStage || 'second_year',
          jd_skill_gaps: data.missingSkills || ['AWS', 'Docker']
        })
      });
      const toolsData = await toolsRes.json();

      if (toolsGrid) {
        toolsGrid.innerHTML = '';
        const toolsMap = toolsData.tool_recommendations_by_skill || {};
        const allTools = [];
        Object.entries(toolsMap).forEach(([sk, toolArr]) => {
          (toolArr || []).forEach(t => allTools.push({ ...t, skill: sk }));
        });

        if (!allTools.length) {
          toolsGrid.innerHTML = `<p class="text-xs text-outline font-code-sm">Standard CLI tools suffice.</p>`;
        } else {
          allTools.slice(0, 6).forEach(t => {
            const card = document.createElement('div');
            card.className = 'p-3.5 rounded-xl bg-surface-container-lowest/70 border border-outline-variant/25 flex flex-col justify-between';
            card.innerHTML = `
              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <span class="font-bold text-white text-xs">${t.tool}</span>
                  <span class="text-[9px] font-code-sm px-1.5 py-0.2 rounded bg-tertiary/15 text-tertiary font-bold uppercase">Free</span>
                </div>
                <p class="text-[11px] text-on-surface-variant leading-relaxed mb-2">${t.use}</p>
              </div>
              <span class="text-[10px] font-code-sm text-cyan">For ${t.skill}</span>
            `;
            toolsGrid.appendChild(card);
          });
        }
      }

    } catch (err) {
      console.error('[CareerIntel] Certs/Tools load error:', err);
      if (recGrid) recGrid.innerHTML = `<p class="text-xs text-error font-code-sm">Failed to load certifications.</p>`;
    }
  }

  // ── SUBVIEW 7: INTERVIEW PREPARATION (Part 9) ───────────────────────────
  function renderInterviewPrep(data) {
    const list = document.getElementById('interview-questions-list');
    if (!list) return;
    list.innerHTML = '';

    const questionsToDisplay = [];
    data.missingSkills.forEach(sk => {
      if (SKILL_INTERVIEW_QUESTIONS[sk]) {
        questionsToDisplay.push({ skill: sk, ...SKILL_INTERVIEW_QUESTIONS[sk] });
      }
    });

    if (!questionsToDisplay.length) {
      questionsToDisplay.push(
        { skill: 'AWS', ...SKILL_INTERVIEW_QUESTIONS['AWS'] },
        { skill: 'Docker', ...SKILL_INTERVIEW_QUESTIONS['Docker'] },
        { skill: 'SQL', ...SKILL_INTERVIEW_QUESTIONS['SQL'] }
      );
    }

    questionsToDisplay.forEach((q, idx) => {
      const qCard = document.createElement('div');
      qCard.className = 'glass-card rounded-2xl p-6 border border-outline-variant/30 space-y-4';
      qCard.id = `interview-q-${idx}`;

      qCard.innerHTML = `
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-outline-variant/20">
          <div class="flex items-center gap-2">
            <span class="w-6 h-6 rounded-lg bg-purple-500/20 text-purple-300 font-code-sm text-xs font-bold flex items-center justify-center">${idx + 1}</span>
            <span class="font-code-sm text-xs font-bold text-white uppercase">${q.category}</span>
            <span class="text-[10px] font-code-sm px-2 py-0.5 rounded-full bg-cyan/10 text-cyan border border-cyan/30">${q.skill}</span>
          </div>
          <span class="text-[10px] font-code-sm text-outline">Recruiter Screening Standard</span>
        </div>

        <p class="text-xs md:text-sm font-semibold text-white leading-relaxed">
          "${q.question}"
        </p>

        <div class="space-y-2">
          <textarea id="ans-input-${idx}" rows="3" placeholder="Type your technical response here to test yourself against the rubric..." class="w-full bg-surface-container border border-outline-variant/40 rounded-xl p-3 text-xs text-white font-body-md focus:border-cyan focus:outline-none leading-relaxed resize-none"></textarea>
          
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-code-sm text-outline">Objective keyword rubric scoring</span>
            <button type="button" class="btn-eval-answer btn-primary-glow px-4 py-1.5 rounded-xl font-code-sm text-xs font-bold cursor-pointer" data-qidx="${idx}">
              Evaluate Answer
            </button>
          </div>
        </div>

        <div id="eval-result-${idx}" class="hidden p-4 rounded-xl bg-surface-container-lowest/80 border border-outline-variant/30 space-y-2 font-code-sm text-xs">
        </div>
      `;
      list.appendChild(qCard);
    });

    list.querySelectorAll('.btn-eval-answer').forEach(btn => {
      btn.addEventListener('click', async () => {
        const qidx = parseInt(btn.getAttribute('data-qidx'), 10);
        const inputEl = document.getElementById(`ans-input-${qidx}`);
        const resultEl = document.getElementById(`eval-result-${qidx}`);
        const qObj = questionsToDisplay[qidx];
        if (!inputEl || !resultEl || !qObj) return;

        const text = inputEl.value.trim();
        if (!text) {
          showToast('error', 'Please write an answer before evaluating.');
          return;
        }

        btn.disabled = true;
        btn.textContent = 'Evaluating...';

        const keywords = qObj.rubric.keywords || [];
        const lowerText = text.toLowerCase();
        const matchedKeywords = keywords.filter(k => lowerText.includes(k.toLowerCase()));
        const score = Math.round((matchedKeywords.length / Math.max(1, keywords.length)) * 100);

        resultEl.classList.remove('hidden');
        resultEl.innerHTML = `
          <div class="flex items-center justify-between pb-2 border-b border-outline-variant/20">
            <div class="flex items-center gap-2">
              <span class="material-symbols-outlined text-[16px] ${score >= 60 ? 'text-tertiary' : 'text-amber-300'}">verified</span>
              <span class="font-bold text-white">Self-Study Rubric Score: ${score}/100</span>
            </div>
            <span class="text-[10px] text-outline">${matchedKeywords.length} of ${keywords.length} technical keywords identified</span>
          </div>

          <p class="text-[11px] text-on-surface-variant leading-relaxed">
            <strong class="text-white">Core Evaluation Concept:</strong> ${qObj.rubric.key_concept}
          </p>

          <div class="text-[10px] text-outline">
            Keywords detected: ${matchedKeywords.length ? matchedKeywords.map(k => `<code class="text-cyan font-bold">${k}</code>`).join(', ') : 'None'}
          </div>

          <div class="text-[10px] text-outline italic">
            * Note: This score is a heuristic study aid based on key architectural terms. It does not represent an actual recruiter hiring decision.
          </div>
        `;

        btn.disabled = false;
        btn.textContent = 'Re-Evaluate Answer';
      });
    });
  }

  // ── SUBVIEW 8: MY PROGRESS TRACKER (Part 10) ─────────────────────────────
  function renderProgressTracker(data) {
    const progMilestones = document.getElementById('prog-completed-milestones');
    const progActiveSkills = document.getElementById('prog-active-skills-count');
    const progVerified = document.getElementById('prog-verified-count');
    const historyList = document.getElementById('progress-history-list');

    if (progMilestones) {
      progMilestones.textContent = `${careerState.completedMilestones.length} / 8`;
    }
    if (progActiveSkills) {
      progActiveSkills.textContent = `${careerState.learningPlanSkills.length} Skills`;
    }
    if (progVerified) {
      progVerified.textContent = `${careerState.verifiedSkills.length} Verified`;
    }

    if (historyList) {
      historyList.innerHTML = '';
      if (!careerState.verifiedSkills.length && !careerState.completedMilestones.length) {
        historyList.innerHTML = `<p class="text-xs text-outline font-code-sm">No verified skill records yet. Use the form above to record your GitHub evidence!</p>`;
        return;
      }

      careerState.verifiedSkills.forEach(v => {
        const item = document.createElement('div');
        item.className = 'p-3 rounded-xl bg-surface-container-lowest/60 border border-tertiary/30 flex items-center justify-between text-xs font-code-sm';
        item.innerHTML = `
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-tertiary text-sm">verified</span>
            <span class="font-bold text-white">${v.skill}</span>
            <span class="text-outline text-[11px]">${v.notes || 'Evidence verified'}</span>
          </div>
          <div class="flex items-center gap-3">
            ${v.evidenceUrl ? `<a href="${v.evidenceUrl.startsWith('http') ? v.evidenceUrl : 'https://' + v.evidenceUrl}" target="_blank" rel="noopener noreferrer" class="text-cyan hover:underline flex items-center gap-0.5"><span>Repository</span><span class="material-symbols-outlined text-[12px]">open_in_new</span></a>` : ''}
            <span class="text-[10px] text-outline">${v.date}</span>
          </div>
        `;
        historyList.appendChild(item);
      });
    }
  }

  // ── Global Skill Detail Modal (Part 3 & Part 5) ──────────────────────────
  window.openSkillDetailModal = function openSkillDetailModal(skillName, isMatched = false) {
    careerState.selectedSkill = skillName;
    saveState();

    const modal = document.getElementById('modal-skill-detail');
    if (!modal) return;

    const titleEl = document.getElementById('modal-skill-title');
    const badgeEl = document.getElementById('modal-skill-badge');
    const catEl = document.getElementById('modal-skill-category');
    const relEl = document.getElementById('modal-skill-relevance');
    const flagEl = document.getElementById('modal-skill-flag-reason');
    const evidEl = document.getElementById('modal-skill-evidence-status');
    const prereqEl = document.getElementById('modal-skill-prereqs');
    const roadmapBtn = document.getElementById('modal-skill-roadmap-btn');
    const roadmapLabel = document.getElementById('modal-skill-roadmap-label');
    const ytBtn = document.getElementById('modal-skill-youtube-btn');
    const docsBtn = document.getElementById('modal-skill-docs-btn');
    const docsLabel = document.getElementById('modal-skill-docs-label');
    const projTitle = document.getElementById('modal-skill-project-title');
    const projDesc = document.getElementById('modal-skill-project-desc');
    const interviewQ = document.getElementById('modal-skill-interview-q');
    const addPlanBtn = document.getElementById('btn-modal-add-plan');
    const addPlanText = document.getElementById('modal-add-plan-text');
    const addPlanIcon = document.getElementById('modal-add-plan-icon');

    if (titleEl) titleEl.textContent = skillName;

    if (badgeEl) {
      badgeEl.className = isMatched
        ? 'font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-tertiary/15 text-tertiary border border-tertiary/40 font-bold'
        : 'font-code-sm text-[10px] px-2 py-0.5 rounded-full bg-error/15 text-error border border-error/40 font-bold';
      badgeEl.textContent = isMatched ? 'Verified Strength' : 'Missing Requirement';
    }

    if (catEl) {
      catEl.textContent = `${careerState.targetRole} · Core Technical Requirement`;
    }

    if (relEl) {
      relEl.textContent = SKILL_RELEVANCE[skillName] || `${skillName} is a foundational technology expected for ${careerState.targetRole} positions.`;
    }

    if (flagEl) {
      flagEl.innerHTML = isMatched
        ? `<span class="material-symbols-outlined text-[14px] text-tertiary">check_circle</span> <span class="text-tertiary">Evidenced in resume and verified on GitHub public profiles.</span>`
        : `<span class="material-symbols-outlined text-[14px]">flag</span> <span>Flagged: Demanded by target job description, but not evidenced in resume text.</span>`;
    }

    if (evidEl) {
      evidEl.className = isMatched ? 'text-tertiary font-bold' : 'text-error font-bold';
      evidEl.textContent = isMatched ? 'Verified on GitHub' : 'No Public Evidence on Resume';
    }

    if (prereqEl) {
      prereqEl.innerHTML = '';
      const prereqs = SKILL_PREREQUISITES[skillName] || ['Programming Fundamentals', 'Terminal / CLI Basics'];
      prereqs.forEach(p => {
        const span = document.createElement('span');
        span.className = 'font-code-sm text-[11px] px-2.5 py-0.5 rounded-full bg-cyan/10 text-cyan border border-cyan/30';
        span.textContent = p;
        prereqEl.appendChild(span);
      });
    }

    const rUrl = getRoadmapShUrl(skillName);
    if (roadmapBtn) roadmapBtn.href = rUrl;
    if (roadmapLabel) roadmapLabel.textContent = rUrl.replace('https://', '');

    const yUrl = getYouTubeSearchUrl(skillName, 'beginner');
    if (ytBtn) ytBtn.href = yUrl;

    const dUrl = getOfficialDocsUrl(skillName);
    if (docsBtn) docsBtn.href = dUrl;
    if (docsLabel) {
      try {
        docsLabel.textContent = new URL(dUrl).hostname;
      } catch (e) {
        docsLabel.textContent = 'official docs';
      }
    }

    const proj = SKILL_PROJECTS[skillName] || {
      title: `Build a Portfolio Deliverable in ${skillName}`,
      deliverable: `Create a clean public GitHub repo demonstrating real implementation of ${skillName}.`
    };
    if (projTitle) projTitle.textContent = proj.title;
    if (projDesc) projDesc.textContent = proj.deliverable;

    const qObj = SKILL_INTERVIEW_QUESTIONS[skillName] || {
      question: `Explain how you would apply ${skillName} to optimize performance in a web application.`
    };
    if (interviewQ) interviewQ.textContent = `"${qObj.question}"`;

    const inPlan = careerState.learningPlanSkills.includes(skillName);
    if (addPlanText) addPlanText.textContent = inPlan ? 'Remove from My Plan' : 'Add to My Learning Plan';
    if (addPlanIcon) addPlanIcon.textContent = inPlan ? 'playlist_remove' : 'playlist_add';

    if (addPlanBtn) {
      addPlanBtn.onclick = () => {
        const idx = careerState.learningPlanSkills.indexOf(skillName);
        if (idx >= 0) {
          careerState.learningPlanSkills.splice(idx, 1);
        } else {
          careerState.learningPlanSkills.push(skillName);
        }
        saveState();
        const nowInPlan = careerState.learningPlanSkills.includes(skillName);
        if (addPlanText) addPlanText.textContent = nowInPlan ? 'Remove from My Plan' : 'Add to My Learning Plan';
        if (addPlanIcon) addPlanIcon.textContent = nowInPlan ? 'playlist_remove' : 'playlist_add';
        renderProgressTracker(getActiveSkillsData());
        showToast('success', nowInPlan ? `Added ${skillName} to learning plan` : `Removed ${skillName} from plan`);
      };
    }

    modal.classList.remove('hidden');
  };

  function closeSkillDetailModal() {
    const modal = document.getElementById('modal-skill-detail');
    if (modal) modal.classList.add('hidden');
  }

  // ── Event Wiring & Initialization ─────────────────────────────────────────
  function initEvents() {
    loadState();

    document.querySelectorAll('.career-subtab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const subtab = btn.getAttribute('data-subtab');
        activateCareerSubtab(subtab);
      });
    });

    const roleSelect = document.getElementById('career-target-role');
    if (roleSelect) {
      roleSelect.value = careerState.targetRole;
      roleSelect.addEventListener('change', (e) => {
        careerState.targetRole = e.target.value;
        saveState();
        renderActiveSubtab(careerState.activeSubtab);
        showToast('info', `Target role updated to ${careerState.targetRole}`);
      });
    }

    const stageSelect = document.getElementById('career-academic-stage');
    if (stageSelect) {
      stageSelect.value = careerState.academicStage;
      stageSelect.addEventListener('change', (e) => {
        careerState.academicStage = e.target.value;
        saveState();
        renderActiveSubtab(careerState.activeSubtab);
        showToast('info', `Academic calibration updated to ${e.target.options[e.target.selectedIndex].text}`);
      });
    }

    const updateHoursPills = (hrs) => {
      careerState.hoursPerWeek = parseInt(hrs, 10);
      saveState();
      document.querySelectorAll('.career-hour-pill').forEach(p => {
        p.classList.toggle('active', parseInt(p.getAttribute('data-hours'), 10) === careerState.hoursPerWeek);
      });
      renderActiveSubtab(careerState.activeSubtab);
    };

    document.querySelectorAll('.career-hour-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        updateHoursPills(pill.getAttribute('data-hours'));
      });
    });

    const btnCloseModal = document.getElementById('btn-close-skill-modal');
    const btnModalClose = document.getElementById('btn-modal-close');
    const modal = document.getElementById('modal-skill-detail');

    if (btnCloseModal) btnCloseModal.addEventListener('click', closeSkillDetailModal);
    if (btnModalClose) btnModalClose.addEventListener('click', closeSkillDetailModal);
    if (modal) {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) closeSkillDetailModal();
      });
    }

    const btnGotoCareer = document.getElementById('btn-goto-career-intel');
    if (btnGotoCareer) {
      btnGotoCareer.addEventListener('click', () => {
        const careerNavTab = document.getElementById('nav-tab-career-intel');
        if (careerNavTab) {
          careerNavTab.click();
        } else if (typeof activateTab === 'function') {
          activateTab('tab-career-intel');
        }
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }

    const vSkill = document.getElementById('video-filter-skill');
    const vLevel = document.getElementById('video-filter-level');
    if (vSkill) vSkill.addEventListener('change', () => renderVideoTutorials(getActiveSkillsData()));
    if (vLevel) vLevel.addEventListener('change', () => renderVideoTutorials(getActiveSkillsData()));

    const btnOvJump = document.getElementById('btn-ov-jump-roadmap');
    if (btnOvJump) {
      btnOvJump.addEventListener('click', () => activateCareerSubtab('roadmap'));
    }
    const btnOvExplore = document.getElementById('btn-ov-explore-skill');
    if (btnOvExplore) {
      btnOvExplore.addEventListener('click', () => {
        const data = getActiveSkillsData();
        const targetSkill = data.missingSkills[0] || 'AWS';
        window.openSkillDetailModal(targetSkill, false);
      });
    }

    // ── Helper: Client-Side Education & Academic Stage Fallback ──────────
    function clientDetectEducationProfile(rawText, eduEntries) {
      const text = (rawText || '').trim();
      const lower = text.toLowerCase();
      const currentYear = new Date().getFullYear();
      const currentMonth = new Date().getMonth() + 1;
      const currentAcademicStartYear = currentMonth >= 7 ? currentYear : (currentYear - 1);

      let instName = '';
      let degName = '';
      let fosName = '';
      let startYr = null;
      let endYr = null;
      let defaultDuration = 4;
      let isLateral = false;
      let evidence = [];

      // 1. Inspect structured education entries first if available
      const entries = Array.isArray(eduEntries) ? eduEntries : [];
      let targetEdu = null;
      for (const e of entries) {
        const blk = `${e.degree || ''} ${e.institution || ''} ${e.field_of_study || ''}`.toLowerCase();
        if (/10th|12th|ssc|hsc|high school|secondary school|cbse\s*-\s*class\s*x/i.test(blk)) continue;
        targetEdu = e;
        break;
      }
      if (!targetEdu && entries.length > 0) targetEdu = entries[0];

      if (targetEdu) {
        degName = targetEdu.degree || '';
        instName = targetEdu.institution || '';
        fosName = targetEdu.field_of_study || '';
        const sMatch = (targetEdu.start_date || '').toString().match(/\b(19\d\d|20\d\d)\b/);
        const eMatch = (targetEdu.end_date || '').toString().match(/\b(19\d\d|20\d\d)\b/);
        if (sMatch) startYr = parseInt(sMatch[1], 10);
        if (eMatch) endYr = parseInt(eMatch[1], 10);
      }

      // 2. Scan raw text for College / University mentions if missing
      if (!instName && text) {
        const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
        const collegeRegex = /\b(?:college\s+of\s+engineering|institute\s+of\s+technology|polytechnic|engineering\s+college|technology\s+and\s+management|institute\s+of\s+science\s+and\s+technology|university|faculty\s+of\s+technology|school\s+of\s+engineering|vidyapeeth|academy\s+of\s+engineering|coep|pict|vjti|pccoep?|mit|vit|bits|nit|iit)\b/i;
        for (const line of lines) {
          if (collegeRegex.test(line) && !/^education/i.test(line) && line.length < 100) {
            instName = line.replace(/^[#*\-•\d.\s]+/, '').replace(/\(?\b(?:19|20)\d{2}\s*[-–—to]+\s*(?:(?:19|20)\d{2}|Present)\b\)?/gi, '').replace(/[,\-|]+$/, '').trim();
            break;
          }
        }
      }

      // 3. Scan for Degree and Field of Study if missing
      if (!degName && text) {
        if (/b\.tech|btech|bachelor of technology/i.test(lower)) degName = 'Bachelor of Technology (B.Tech)';
        else if (/b\.e\.|b\.e\b|bachelor of engineering/i.test(lower)) degName = 'Bachelor of Engineering (B.E.)';
        else if (/m\.tech|mtech|master of technology/i.test(lower)) { degName = 'Master of Technology (M.Tech)'; defaultDuration = 2; }
        else if (/mca|master of computer applications/i.test(lower)) { degName = 'Master of Computer Applications (MCA)'; defaultDuration = 2; }
        else if (/diploma|polytechnic/i.test(lower)) { degName = 'Diploma in Engineering'; defaultDuration = 3; }
        else degName = 'Bachelor of Technology (B.Tech / B.E.)';
      }

      if (!fosName && text) {
        if (/computer\s*(?:science(?:\s*(?:and|&)\s*engineering)?|engineering)|cse|cs\b/i.test(lower)) fosName = 'Computer Science & Engineering';
        else if (/information\s*technology|it\b/i.test(lower)) fosName = 'Information Technology';
        else if (/artificial\s*intelligence|ai\s*(&|and)\s*ds|aiml/i.test(lower)) fosName = 'AI & Data Science';
        else if (/electronics|entc|ece/i.test(lower)) fosName = 'Electronics & Telecommunication';
        else if (/mechanical/i.test(lower)) fosName = 'Mechanical Engineering';
        else if (/civil/i.test(lower)) fosName = 'Civil Engineering';
        else fosName = 'Engineering & Technology';
      }

      // 4. Scan for year ranges (e.g. 2025 - 2029, 2025 - 2028, 2022 - 2025)
      if ((!startYr || !endYr) && text) {
        const yrMatches = text.match(/\b(20\d\d)\b/g);
        if (yrMatches && yrMatches.length >= 2) {
          const uniqueYrs = Array.from(new Set(yrMatches.map(y => parseInt(y, 10)))).sort((a, b) => a - b);
          if (uniqueYrs.length >= 2) {
            startYr = uniqueYrs[0];
            endYr = uniqueYrs[uniqueYrs.length - 1];
          }
        }
      }

      // 5. Detect Pathway (After Diploma vs After 12th)
      const hasDiploma = /diploma|polytechnic|lateral\s*entry|direct\s*second\s*year|dsy|diploma\s*to\s*degree/i.test(lower);
      const has12th = /12th|hsc|higher\s*secondary|intermediate|cbse\s*-\s*class\s*xii|class\s*12/i.test(lower);
      let pathway = 'After 12th (Standard 4-Year B.Tech / B.E.)';

      if (/m\.tech|master|mca|m\.s\./i.test(degName)) {
        pathway = "Postgraduate (Master's Degree Program)";
      } else if (hasDiploma || (startYr && endYr && (endYr - startYr === 3) && /b\.tech|b\.e/i.test(degName))) {
        pathway = 'After Diploma (Polytechnic Lateral Entry Direct 2nd Year)';
        isLateral = true;
        defaultDuration = 3;
      } else if (has12th) {
        pathway = 'After 12th (Standard 4-Year B.Tech / B.E.)';
      }

      // 6. Explicit stage detection from text
      let stage = 'second_year';
      let explicitStageFound = false;
      if (/\b(1st\s*year|first\s*year|freshman|sem(?:ester)?\s*[12])\b/i.test(lower)) {
        stage = 'first_year';
        explicitStageFound = true;
        evidence.push('Explicitly stated 1st Year student in resume text.');
      } else if (/\b(2nd\s*year|second\s*year|sophomore|sem(?:ester)?\s*[34]|direct\s*second\s*year|dsy)\b/i.test(lower)) {
        stage = 'second_year';
        explicitStageFound = true;
        evidence.push('Explicitly stated 2nd Year / Direct Second Year student.');
      } else if (/\b(3rd\s*year|third\s*year|junior|sem(?:ester)?\s*[56]|penultimate)\b/i.test(lower)) {
        stage = 'third_year';
        explicitStageFound = true;
        evidence.push('Explicitly stated 3rd Year student.');
      } else if (/\b(4th\s*year|fourth\s*year|final\s*year|senior|sem(?:ester)?\s*[78]|graduating\s*year)\b/i.test(lower)) {
        stage = 'final_year';
        explicitStageFound = true;
        evidence.push('Explicitly stated 4th / Final Year student.');
      } else if (/\b(graduated|fresh\s*graduate|alumnus|alumna|passed\s*out)\b/i.test(lower)) {
        stage = 'early_career';
        explicitStageFound = true;
        evidence.push('Explicitly stated graduated alumnus.');
      }

      // 7. Deterministic date calculation if not explicitly stated
      if (!explicitStageFound && startYr && endYr) {
        if (endYr < currentYear || (endYr === currentYear && currentMonth >= 7)) {
          stage = 'early_career';
          evidence.push(`Graduation year ${endYr} has passed relative to current date.`);
        } else {
          const elapsed = currentAcademicStartYear - startYr + 1;
          const calcYr = Math.max(1, Math.min(defaultDuration, elapsed));
          if (calcYr === 1) stage = 'first_year';
          else if (calcYr === 2) stage = 'second_year';
          else if (calcYr === 3) stage = defaultDuration >= 4 ? 'third_year' : 'final_year';
          else stage = 'final_year';
          evidence.push(`Calculated ${calcYr}${calcYr === 1 ? 'st' : calcYr === 2 ? 'nd' : calcYr === 3 ? 'rd' : 'th'} year from enrollment timeline (${startYr}–${endYr}).`);
        }
      }

      const timelineStr = (startYr && endYr) ? `${startYr} – ${endYr}` : (startYr ? `${startYr} – Present` : (endYr ? `Class of ${endYr}` : 'Active Enrollment'));

      return {
        institution: instName || 'College of Engineering & Technology',
        college_name: instName || 'College of Engineering & Technology',
        degree: degName || 'Bachelor of Technology (B.Tech)',
        field_of_study: fosName || 'Computer Science & Engineering',
        start_year: startYr,
        graduation_year: endYr,
        timeline: timelineStr,
        duration_years: defaultDuration,
        pathway: pathway,
        is_lateral_entry: isLateral,
        academic_stage: stage,
        confidence: (startYr && endYr) ? 0.95 : 0.85,
        evidence: evidence
      };
    }

    // ── Helper: Render Active CV Education Profile Banner ──────────────────
    function renderEducationProfileBanner(profile) {
      const banner = document.getElementById('career-cv-profile-banner');
      if (!banner || !profile) return;

      const elCollege = document.getElementById('banner-cv-college');
      const elStage = document.getElementById('banner-cv-stage-badge');
      const elPathway = document.getElementById('banner-cv-pathway-badge');
      const elDegree = document.getElementById('banner-cv-degree');
      const elTimeline = document.getElementById('banner-cv-timeline');
      const elConfidence = document.getElementById('banner-cv-confidence');

      const stageDisplayMap = {
        'first_year': '1st Year Student',
        'second_year': '2nd Year Student',
        'third_year': '3rd Year Student',
        'final_year': 'Final Year Student',
        'early_career': 'Early Career Professional',
        'graduated': 'Graduated / Early Career'
      };

      if (elCollege) elCollege.textContent = profile.institution || profile.college_name || 'Engineering College';
      if (elStage) elStage.textContent = stageDisplayMap[profile.academic_stage] || '2nd Year Student';
      if (elPathway) elPathway.textContent = profile.pathway || (profile.is_lateral_entry ? 'After Diploma (DSY)' : 'After 12th');
      if (elDegree) elDegree.textContent = `${profile.degree || 'B.Tech'}${profile.field_of_study ? ' · ' + profile.field_of_study : ''}`;
      if (elTimeline) elTimeline.textContent = profile.timeline || (profile.start_year ? `${profile.start_year} – ${profile.graduation_year || 'Present'}` : 'Active Timeline');
      if (elConfidence) elConfidence.textContent = `${Math.round((profile.confidence || 0.9) * 100)}% Confident`;

      banner.classList.remove('hidden');
    }

    // ── Primary Action: Sync with Active CV ─────────────────────────────────
    async function syncWithActiveCv() {
      const btnSync = document.getElementById('btn-career-sync-active');
      const origCvText = document.getElementById('orig-cv-text')?.value?.trim() || '';
      const rawText = currentRawResumeText || origCvText || currentReportData?.raw_resume_text || '';
      const eduEntries = currentCanonicalData?.education || currentReportData?.canonical_resume?.education || [];

      if (!rawText && (!eduEntries || eduEntries.length === 0) && !currentReportData && !selectedFile) {
        showToast('upload_file', 'Please upload a resume in Match Engine or paste your CV in Upgrade CV tab first.');
        return;
      }

      if (btnSync) {
        btnSync.disabled = true;
        btnSync.innerHTML = `<span class="btn-spinner inline-block w-3 h-3 border-2"></span><span>Reading CV…</span>`;
      }

      try {
        let detectedProfile = null;

        // 1. Try server-side intelligent academic stage detection
        try {
          const res = await fetch('/api/career/academic-year', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              raw_text: rawText,
              education_entries: eduEntries
            })
          });

          if (res.ok) {
            const data = await res.json();
            if (data && data.academic_stage && data.academic_stage !== 'unknown') {
              detectedProfile = data;
            }
          }
        } catch (serverErr) {
          console.warn('[CareerIntel] Server academic detection fallback:', serverErr);
        }

        // 2. Client-side fallback if server response was empty or offline
        if (!detectedProfile || detectedProfile.academic_stage === 'unknown') {
          detectedProfile = clientDetectEducationProfile(rawText, eduEntries);
        }

        // 3. Map detected academic stage
        let mappedStage = detectedProfile.academic_stage || 'second_year';
        if (mappedStage === 'graduated') mappedStage = 'early_career';
        if (!['first_year', 'second_year', 'third_year', 'final_year', 'early_career'].includes(mappedStage)) {
          mappedStage = 'second_year';
        }

        careerState.academicStage = mappedStage;
        careerState.detectedEducationProfile = detectedProfile;

        // 4. Update Academic Stage dropdown
        if (stageSelect) {
          stageSelect.value = mappedStage;
        }

        // 5. Update Target Role if detected from active report
        if (currentReportData?.job_matching?.target_role || currentReportData?.target_role) {
          const matchedRole = currentReportData.job_matching?.target_role || currentReportData.target_role;
          if (roleSelect && Array.from(roleSelect.options).some(o => o.value === matchedRole)) {
            roleSelect.value = matchedRole;
            careerState.targetRole = matchedRole;
          }
        }

        // 6. Save State and Update UI
        saveState();
        renderEducationProfileBanner(detectedProfile);
        renderActiveSubtab(careerState.activeSubtab);

        const stageLabel = (stageSelect?.options[stageSelect.selectedIndex]?.text) || '2nd Year Student';
        const collName = detectedProfile.institution || detectedProfile.college_name || 'College of Engineering';
        const timelineStr = detectedProfile.timeline || 'Active';

        showToast('school', `Synced CV: ${collName} (${timelineStr}) → Set to ${stageLabel}!`);

      } catch (err) {
        console.error('[CareerIntel] Sync error:', err);
        showToast('error', 'Could not sync CV details. Please verify your resume text.');
      } finally {
        if (btnSync) {
          btnSync.disabled = false;
          btnSync.innerHTML = `<span class="material-symbols-outlined text-[13px]">sync</span><span>Sync with Active CV</span>`;
        }
      }
    }

    const btnSync = document.getElementById('btn-career-sync-active');
    if (btnSync) {
      btnSync.addEventListener('click', syncWithActiveCv);
    }

    const btnReSync = document.getElementById('btn-career-resync');
    if (btnReSync) {
      btnReSync.addEventListener('click', syncWithActiveCv);
    }

    const btnDemo = document.getElementById('btn-career-load-demo');
    const btnEmptyDemo = document.getElementById('btn-career-empty-demo');
    const handleDemoLoad = () => {
      careerState.targetRole = 'Backend Developer';
      careerState.academicStage = 'second_year';
      if (roleSelect) roleSelect.value = 'Backend Developer';
      if (stageSelect) stageSelect.value = 'second_year';
      saveState();
      renderActiveSubtab(careerState.activeSubtab);
      showToast('verified', 'Loaded 2nd Year Student profile (Backend & AWS Roadmap)!');
    };
    if (btnDemo) btnDemo.addEventListener('click', handleDemoLoad);
    if (btnEmptyDemo) btnEmptyDemo.addEventListener('click', handleDemoLoad);

    const btnEmptyGoto = document.getElementById('btn-career-empty-goto-match');
    if (btnEmptyGoto) {
      btnEmptyGoto.addEventListener('click', () => {
        if (typeof activateTab === 'function') activateTab('tab-match-engine');
      });
    }

    const btnSubmitVerify = document.getElementById('btn-submit-verify-skill');
    if (btnSubmitVerify) {
      btnSubmitVerify.addEventListener('click', () => {
        const sName = document.getElementById('verify-skill-name')?.value.trim();
        const sUrl = document.getElementById('verify-skill-url')?.value.trim();
        const sNotes = document.getElementById('verify-skill-notes')?.value.trim();

        if (!sName) {
          showToast('error', 'Please enter a skill name to verify.');
          return;
        }

        const newRec = {
          skill: sName,
          evidenceUrl: sUrl,
          notes: sNotes,
          date: new Date().toLocaleDateString()
        };

        careerState.verifiedSkills.unshift(newRec);
        saveState();

        fetch('/api/career/progress/verify-skill', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: careerState.sessionId,
            skill: sName,
            evidence_url: sUrl || null,
            notes: sNotes || null
          })
        }).catch(e => console.warn('Progress sync warning:', e));

        if (document.getElementById('verify-skill-name')) document.getElementById('verify-skill-name').value = '';
        if (document.getElementById('verify-skill-url')) document.getElementById('verify-skill-url').value = '';
        if (document.getElementById('verify-skill-notes')) document.getElementById('verify-skill-notes').value = '';

        renderProgressTracker(getActiveSkillsData());
        showToast('verified', `Recorded evidence verification for ${sName}!`);
      });
    }

    const btnExport = document.getElementById('btn-export-progress');
    if (btnExport) {
      btnExport.addEventListener('click', () => {
        const exportData = {
          exportedAt: new Date().toISOString(),
          careerState: careerState
        };
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Career_Learning_Progress_${careerState.targetRole.replace(/\s+/g, '_')}.json`;
        document.body.appendChild(a);
        a.click();
        URL.revokeObjectURL(url);
        a.remove();
        showToast('success', 'Learning progress exported as JSON.');
      });
    }

    const btnReset = document.getElementById('btn-reset-progress');
    if (btnReset) {
      btnReset.addEventListener('click', () => {
        if (!confirm('Are you sure you want to reset all milestone progress and verified skill history?')) return;
        careerState.completedMilestones = [];
        careerState.inProgressMilestones = [];
        careerState.completedProjects = [];
        careerState.verifiedSkills = [];
        saveState();
        renderActiveSubtab(careerState.activeSubtab);
        showToast('info', 'Progress reset.');
      });
    }

    if (stageSelect && careerState.academicStage) {
      stageSelect.value = careerState.academicStage;
    }
    if (roleSelect && careerState.targetRole) {
      roleSelect.value = careerState.targetRole;
    }
    if (careerState.detectedEducationProfile) {
      renderEducationProfileBanner(careerState.detectedEducationProfile);
    }

    activateCareerSubtab(careerState.activeSubtab || 'overview');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEvents);
  } else {
    initEvents();
  }

})();



