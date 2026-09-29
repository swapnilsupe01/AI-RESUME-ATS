# AI Resume ATS — Explainable Resume, Project, Identity & Code Forensics System

> **A Penta-Layer AI-powered ATS that semantically matches resumes with job descriptions using Sentence-BERT, verifies technical claims against public GitHub/LinkedIn evidence, defends against candidate fraud, audits codebase originality using 5-dimension forensics, and includes a full AI Resume Upgrade Engine (Layer E) that provides per-suggestion accept/edit/reject review with hallucination-guarded improvements — all running 100% offline without any API keys.**

[![CI/CD & DevSecOps Pipeline](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions/workflows/ci.yml/badge.svg)](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue?logo=docker)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-HPA%20%26%20Probes-326ce5?logo=kubernetes)](https://kubernetes.io/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD%20Pipeline-D24939?logo=jenkins)](https://www.jenkins.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Penta-Layer AI Intelligence Architecture

Unlike traditional ATS systems that rely solely on keyword matching or naive whole-document similarity, this system introduces **five distinct, concurrent intelligence layers**:

```text
                                        ┌───────────────────────────┐
                                        │        Resume PDF         │
                                        └─────────────┬─────────────┘
                                                      │
         ┌──────────────┬───────────────┬─────────────┴────────────┬──────────────────────────────┐
         ▼              ▼               ▼                          ▼                              ▼
Layer A: Job Match  Layer B: Evidence  Layer C: Identity & Fraud  Layer D: Code Forensics        Layer E: Upgrade Engine
┌────────────────┐  ┌────────────────┐ ┌─────────────────────────┐ ┌─────────────────────────┐  ┌─────────────────────────┐
│  JD S-BERT     │  │ GitHub/LinkedIn│ │  Anti-Spoofing Engine   │ │ Anti-Fork / Anti-Temp.  │  │ HF / RAG Suggestions    │
│  Match Score   │  │ Claim Verifier │ │  10-Signal Ownership    │ │  5 Forensic Dimensions  │  │ Hallucination Guard     │
│                │  │                │ │                         │ │                         │  │ Accept / Edit / Reject  │
│  ATS Score     │  │ Evidence Score │ │  Ownership Trust Verdict│ │  Authenticity Score     │  │ ATS-PDF Export          │
└───────┬────────┘  └───────┬────────┘ └────────────┬────────────┘ └────────────┬────────────┘  └──────────┬──────────────┘
        │                   │                        │                           │                          │
        └───────────────────┴────────────────────────┴─────────────┬─────────────┴──────────────────────────┘
                                                                   ▼
                                             ┌───────────────────────────────┐
                                             │    Explainable AI Report +    │
                                             │    Layer E Upgrade Studio     │
                                             │  Per-Suggestion Review & PDF  │
                                             └───────────────────────────────┘
```

---

## 2. Core Features

### 🔹 Layer A — Resume ↔ Job Description Semantic Matching
* **Skill-Level Semantic Matching**: Evaluates each required skill individually using **Sentence-BERT (`all-MiniLM-L6-v2`)** and cosine similarity matrix. Catches semantic equivalencies (e.g. *"FastAPI"* $\leftrightarrow$ *"REST API development"*).
* **Multi-Model Breakdown**: Computes Unigram, Bigram, Trigram N-gram overlaps and TF-IDF metrics.
* **Structured Section & Experience Evaluation**: Assesses education requirements, work history, and section completeness.

### 🔹 Layer B — Resume ↔ Public Project Evidence & Multi-Platform Verification
* **Automatic URL Detection**: Extracts public GitHub repository links, LinkedIn profiles, and portfolio URLs directly from the resume text using strict regex validators.
* **Public Project Evidence Retrieval**: Queries real public repository metadata, languages, dependency files (`requirements.txt`, `package.json`), topics, and README documentation via GitHub REST APIs.
* **Transparent LinkedIn Intelligence**: Transparently parses public profile data when accessible and surfaced cleanly. When LinkedIn anti-bot protection (HTTP 999 / Authwall) blocks automated scrapers, the system explicitly reports the authwall status and provides recruiters with a 1-click verified candidate profile link rather than fabricating synthetic posts or certifications.
* **Claim Extraction**: Deconstructs resume project descriptions into discrete technical claims.
* **3-Tier Evidence Confidence Categorization**:
  * 🟢 **Verified** ($\text{Cosine Similarity} \ge 80\%$): Direct code, metadata, or explicit documentation substantiates the claim.
  * 🟡 **Partially Supported** ($60\% - 79\%$): Related technologies or context exist without direct proof.
  * 🔴 **Not Supported** ($< 60\%$): Little or no evidence found in retrieved public documentation.
* **Discrepancy / Inconsistency Warnings**: Non-accusatory alerts if public code repository dependencies diverge significantly from resume claims.

### 🔹 Layer C — Dual-Track GitHub Identity & Anti-Fraud Architecture
Protects recruiters from candidate fraud where random, stolen, or celebrity GitHub repository URLs are pasted into a resume (e.g. candidate *Swapnil Supe* pasting an unrelated user's GitHub *swapnil-23*):

```text
                    GitHub Identity Verification
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
       Account Control                   Identity Correlation
              │                                 │
         OAuth proof                   LinkedIn ↔ GitHub
         Account ID                    Portfolio ↔ GitHub
         Authenticated User            Name Consistency (4 Signals)
                                       Project Consistency (S-BERT)
```

#### Track 1 — Account Control (Cryptographic & Authenticated Proof)
* **GitHub OAuth 2.0 / PAT Handshake**: Allows candidates to authenticate ownership of their GitHub identity with proof of account control and verified GitHub User ID.
* **Direct Session Linking**: Couples the authenticated account directly to the resume audit.

#### Track 2 — Identity Correlation (9-Signal Heuristic Anti-Spoofing Engine)
1. **GitHub Bio Display Name Match** (18%): Token overlap between GitHub profile name and candidate name.
2. **Username Name Token Overlap** (10%): Fuzzy and substring token overlap between GitHub handle and candidate name.
3. **LinkedIn Cross-Link in GitHub Bio** (18%): Validates whether the GitHub profile bio/blog explicitly points to the candidate's LinkedIn URL.
4. **Git Commit Author Names** (14%): Audits local author signatures in recent Git commits against candidate name.
5. **Account Age vs. Claimed Experience** (10%): Flags discrepancies where a candidate claims 5+ years of senior experience on an account created weeks ago.
6. **Git Commit Author Email Cross-Match** (10%): Scans raw Git commit email headers against resume contact email.
7. **Contribution History Authenticity** (5%): Audits public repository volume, follower counts, and multi-year activity graphs.
8. **Profile README Identity Scan** (5%): Extracts introductory markdown headers (`# Hi, I'm Swapnil`) from `github.com/{user}/{user}/README.md`.
9. **LinkedIn Post → GitHub Cross-Reference** (10%): Analyzes public LinkedIn technical posts to verify if the candidate publicly shared and claimed ownership of the exact GitHub repositories.
* **Ownership Trust Verdict**: Categorized into 🟢 *Ownership Confirmed*, 🟡 *Likely Owner*, 🟠 *Uncertain Ownership*, or 🔴 *Ownership Mismatch (Potential Fraud)* with automatic score penalties for suspicious accounts.

### 🔹 Layer D — 5-Dimension Code Quality & Authenticity Forensics
Answers the critical recruiter question: *"Did this candidate actually write this software, or did they fork someone else's repo, copy a YouTube tutorial, or push a single-commit ZIP dump?"*
1. **Fork & Upstream Origin Check** (25%): Inspects `repo.fork`, parent metadata, and root commit author to catch derivative clones.
2. **Commit Timeline Cadence & Anomaly Model** (25%): Uses unsupervised **Isolation Forest** scoring on commit intervals. Differentiates single-day ZIP dumps from organic multi-week development.
3. **Commit Message Semantic Quality (NER)** (15%): Categorizes commit tags using NLP token classification (`feat`, `fix`, `refactor`, `docs`, `test`) vs lazy placeholders (`update`, `done`).
4. **Tutorial & Boilerplate Fingerprint Scanner** (20%): Regex-scans repo metadata, topics, and READMEs for YouTube, Udemy, Coursera, or FreeCodeCamp starter kit markers.
5. **Production Engineering Rigor** (15%): Audits repository tree for unit tests (`pytest`, `jest`), Docker containerization (`Dockerfile`, `docker-compose`), and CI/CD pipelines (`.github/workflows`, `Jenkinsfile`).

### 🔹 Layer E — AI Resume Upgrade Engine *(New)*
Helps students transform their resume into a tailored, ATS-optimized version against a specific job description — without fabricating any skills, tools, metrics, or achievements.

* **HF Inference or 100% Offline**: Uses Hugging Face Mistral-7B-Instruct when `HF_TOKEN` is configured; automatically falls back to the built-in Sentence-BERT RAG engine with NLP heuristics — **no API key required**.
* **Section-Level AI Suggestions**: Generates specific improvements for the **Professional Summary**, every **Experience bullet point**, and all **Project descriptions**.
* **Evidence Hallucination Guard**: Every suggestion is evaluated against the candidate's original resume before being shown:
  * 🟢 **Supported**: Wording and verb improvements only — safe to accept.
  * 🟡 **Needs Confirmation**: New metrics or business-impact language introduced — candidate must verify.
  * 🔴 **Unsupported**: New tools, certifications, or credentials not found in original — flagged for removal.
* **Per-Suggestion Candidate Control**: Candidate reviews each suggestion individually and can:
  * **Accept** the AI suggestion as-is.
  * **Edit** the suggestion text inline before accepting.
  * **Reject** and keep the original text.
  * **Batch-accept** all `supported` suggestions with one click.
* **Live Approved Preview**: Real-time resume preview updates as candidates make decisions — shows only approved content.
* **ATS-Compliant PDF Export**: Generates a clean, single-column, machine-readable PDF from approved suggestions.
* **Session Isolation**: Each review session is independent with a 2-hour TTL; no resume content is stored beyond the session.

### 🔹 Authentic GitHub GraphQL Contribution Intelligence Engine
* **100% Real GraphQL API Integration**: Directly queries GitHub's GraphQL API (`user.contributionsCollection.contributionCalendar`) across full 52-week calendars, individual contribution days, contribution counts, and colors.
* **Zero-Synthetic-Data Policy**: **Guaranteed 0% fake or mock data.** The system never generates synthetic heatmaps or fabricated activity profiles.
* **Multi-Year Historical Heatmap**: Interactive yearly contribution browser with real-time year switching and authentic commit intensity scaling.
* **Advanced Activity Metrics**: Calculates live current streak, longest streak, total annual contributions, active weeks, and weekend-to-weekday commitment ratios.
* **Repository-Grouped Commit Contribution Analysis**: Queries `commitContributionsByRepository` to expose exactly which public projects the candidate contributed code to.

---

## 3. Explainable Scoring Formulation

### A. Job Match Score (Layer A)
$$\text{Job Match Score} = 0.35 \cdot S_{\text{exact}} + 0.30 \cdot S_{\text{semantic}} + 0.10 \cdot \max(\text{TF-IDF}, \text{N-Gram}) + 0.10 \cdot S_{\text{experience}} + 0.05 \cdot S_{\text{section}} + 0.05 \cdot S_{\text{education}} + 0.05 \cdot S_{\text{doc-semantic}}$$

### B. Project Evidence Score (Layer B)
$$\text{Evidence Score} = 0.50 \cdot E_{\text{GitHub}} + 0.30 \cdot E_{\text{Portfolio}} + 0.20 \cdot C_{\text{Consistency}}$$

### C. Identity Ownership & Anti-Fraud Score (Layer C)
$$\text{Ownership Score} = \sum_{i=1}^{10} \left( \frac{w_i}{\sum_{j \in \text{Available}} w_j} \right) \cdot S_i$$

* **Dynamic Penalty Enforcement**:
  * If $\text{Ownership Score} < 20$ (🔴 *Ownership Mismatch / Spoof Detected*):
    $$\text{Evidence Score}_{\text{penalized}} = \text{Evidence Score} \times 0.20 \quad (-80\% \text{ Penalty})$$
  * If $20 \le \text{Ownership Score} < 50$ (🟠 *Uncertain Ownership*):
    $$\text{Evidence Score}_{\text{penalized}} = \text{Evidence Score} \times 0.60 \quad (-40\% \text{ Penalty})$$

### D. Code Quality & Authenticity Score (Layer D)
$$\text{Authenticity Score} = 0.25 \cdot D_{\text{Fork}} + 0.25 \cdot D_{\text{Cadence}} + 0.15 \cdot D_{\text{CommitNER}} + 0.20 \cdot D_{\text{TutorialScan}} + 0.15 \cdot D_{\text{ProdStandards}}$$

### E. Quad-Layer Profile Synthesis
$$\text{Overall Profile Score} = 0.45 \cdot \text{Job Match} + 0.30 \cdot \text{Evidence Score} + 0.25 \cdot \text{Authenticity Score}$$

---

## 4. Zero-Cost ($0) DevOps, DevSecOps & Cloud Stack

| DevOps Tool | Config File | Purpose |
| :--- | :--- | :--- |
| **Docker** | `Dockerfile` | Multi-stage build with baked-in Sentence-BERT model cache for instant startup. |
| **Docker Compose** | `docker-compose.yml` | One-command local container orchestration with persistent cache. |
| **Kubernetes (K8s)** | `k8s/deployment.yaml`, `k8s/service.yaml`, `k8s/hpa.yaml` | Cloud-native deployment with health probes (`/api/health`) and auto-scaling. |
| **Jenkins CI/CD** | `Jenkinsfile` | Declarative pipeline: Lint $\rightarrow$ Bandit Security $\rightarrow$ Pytest $\rightarrow$ Docker Build $\rightarrow$ Smoke Test. |
| **GitHub Actions** | `.github/workflows/ci.yml` | Automated CI/CD running on every push/PR ($0 cost on public repos). |
| **DevSecOps** | `bandit` | Static Application Security Testing (SAST) for Python code audits. |
| **Observability** | `/metrics` | Prometheus metrics tracking request latency and AI inference duration. |
| **Cloud Hosting** | `Procfile` | Ready for zero-cost deployment on **Sevalla**, **Render**, or **Hugging Face Spaces**. |

---

## 5. Project Directory Structure

```text
AI-Resume-ATS/
├── Dockerfile                      # Multi-stage container build
├── docker-compose.yml              # Local container orchestration
├── Jenkinsfile                     # Jenkins CI/CD pipeline
├── Procfile                        # Cloud PaaS deployment entry
├── .dockerignore
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions CI/CD & DevSecOps
├── k8s/
│   ├── deployment.yaml             # Kubernetes Deployment with probes
│   ├── service.yaml                # Kubernetes Service routing
│   └── hpa.yaml                    # Horizontal Pod Autoscaler
├── backend/
│   ├── run.py                      # Local server entry point
│   ├── test.py                     # End-to-end ML & verification test suite
│   ├── requirements.txt            # Python dependencies
│   └── app/
│       ├── main.py                 # FastAPI app, Prometheus metrics & static mount
│       ├── api/
│       │   ├── routes.py           # /api/analyze, /api/verify-project, /api/health
│       │   └── github_routes.py    # Real GitHub GraphQL contributions, summary & OAuth
│       ├── github/
│       │   ├── graphql_client.py   # GitHub GraphQL query engine (contributionsCollection)
│       │   ├── contribution_service.py # Streaks, busiest day, heatmap & repo contribution metrics
│       │   ├── oauth_service.py    # GitHub OAuth & PAT identity verification
│       │   ├── github_models.py    # Pydantic schemas for real GitHub data
│       │   └── db.py               # Session storage & cached contribution profiles
│       ├── parser/
│       │   ├── pdf_parser.py       # PyMuPDF text & structure extractor
│       │   └── resume_parser.py    # Contact, links & section segmentation
│       ├── extraction/
│       │   ├── skill_extractor.py  # Categorized skill taxonomy extractor
│       │   ├── project_extractor.py# Project block & repo link parser
│       │   └── claim_extractor.py  # Verifiable claim deconstructor
│       ├── evidence/
│       │   ├── url_extractor.py    # GitHub, LinkedIn & Portfolio link parser
│       │   ├── github_analyzer.py  # Real GitHub API metadata & README parser (zero mock data)
│       │   ├── linkedin_analyzer.py# Real LinkedIn profile & authwall-aware parser (zero mock data)
│       │   ├── identity_verifier.py# Layer C 10-signal anti-spoofing ownership verifier
│       │   ├── code_quality_analyzer.py # Layer D 5-dimension code forensics (anti-fork/anti-template)
│       │   ├── portfolio_analyzer.py# Public portfolio HTML parser
│       │   └── project_verifier.py # Sentence-BERT Claim ↔ Evidence Verifier
│       ├── models/
│       │   ├── embedding_model.py  # SentenceTransformer (all-MiniLM-L6-v2)
│       │   ├── skill_embedding_model.py # Fine-grained semantic comparator
│       │   ├── tfidf_model.py      # TF-IDF cosine similarity
│       │   └── ngram_model.py      # Unigram, Bigram, Trigram models
│       ├── matching/
│       │   ├── skill_matcher.py    # Multi-tier exact + semantic skill matching
│       │   ├── semantic_matcher.py # Whole-text semantic alignment
│       │   └── experience_matcher.py# Education & experience evaluation
│       ├── scoring/
│       │   ├── ats_scorer.py       # Job Match Score calculation
│       │   ├── evidence_scorer.py  # Public Project Evidence Score calculation
│       │   └── final_scorer.py     # Dual-intelligence synthesis engine
│       ├── recommendations/
│       │   └── recommendation_engine.py # Actionable dual-track recommendations
│       ├── utils/
│       │   ├── skills.py           # Technical taxonomy & aliases
│       │   └── text_utils.py       # Text cleaning & normalization helpers
│       ├── generation/             # ── Layer E: AI Resume Upgrade Engine ──
│       │   ├── huggingface_client.py  # HF Mistral-7B-Instruct inference client
│       │   ├── hallucination_guard.py # Evidence-based claim validator
│       │   ├── suggestion_manager.py  # Session + accept/edit/reject workflow (TTL 2h)
│       │   └── resume_upgrade_engine.py # Orchestrator for summary/experience/projects
│       ├── api/
│       │   ├── upgrade_routes.py   # Layer E REST API (7 endpoints)
│       │   └── routes.py           # Existing core analysis routes
│       └── static/
│           ├── index.html          # Full 5-layer web UI + Layer E Studio tab
│           ├── style.css           # Dark glassmorphism theme + suggestion cards
│           └── app.js              # Heatmap, transform, and suggestion review controller
├── dataset/
│   ├── generate_sample_pdf.py      # Sample resume PDF generator
│   ├── job_descriptions/
│   └── resumes/
└── tests/
    ├── test_parser.py
    ├── test_matching.py
    ├── test_evidence.py
    ├── test_scoring.py
    └── test_layer_e.py             # Layer E unit + integration tests
```

---

## 6. Key REST & GraphQL API Endpoints

### Core Analysis & Evidence

| Endpoint | Method | Purpose | Data Source |
| :--- | :--- | :--- | :--- |
| `/api/analyze` | `POST` | Full Penta-Layer evaluation (S-BERT matching, evidence, identity audit, code forensics). | Multi-Model + Multi-API |
| `/api/verify-project` | `POST` | On-demand verification of a single GitHub repository against resume claims. | GitHub REST API + S-BERT |
| `/api/github/contributions` | `GET` | Fetches authentic 52-week contribution calendar for a given year. | **GitHub GraphQL API** |
| `/api/github/summary` | `GET` | Computes live streaks, busiest day, total annual contributions & active weeks. | **GitHub GraphQL API** |
| `/api/github/oauth/status` | `GET` | Checks if candidate has an active authenticated GitHub session. | GitHub OAuth Engine |
| `/api/github/oauth/token` | `POST` | Verifies PAT or OAuth code for higher rate-limits (5,000 req/hr). | GitHub API Identity Check |
| `/api/health` | `GET` | System health probe (Docker & Kubernetes readiness/liveness checks). | Internal |
| `/metrics` | `GET` | Prometheus telemetry tracking request throughput & AI inference latency. | Prometheus Middleware |

### Layer E — AI Resume Upgrade Engine

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/upgrade/hf-status` | `GET` | Hugging Face model readiness & token configuration check |
| `/api/upgrade/generate-suggestions` | `POST` | Ingest resume + JD, run upgrade engine & hallucination guard, return structured suggestions |
| `/api/upgrade/accept-suggestion` | `POST` | Accept a suggestion (with optional inline candidate text override) |
| `/api/upgrade/reject-suggestion` | `POST` | Reject a suggestion and preserve original resume text |
| `/api/upgrade/approved-resume` | `GET` | Retrieve canonical resume + Markdown applying **only** accepted suggestions |
| `/api/upgrade/export-pdf` | `POST` | Generate ATS-compliant single-column PDF from the approved session resume |
| `/api/upgrade/session-status` | `GET` | Retrieve session review statistics (total / pending / accepted / rejected / evidence counts) |


---

## 7. Quickstart & Installation

### Option 1: Run with Python Locally
```bash
# 1. Clone repository
git clone https://github.com/swapnilsupe01/AI-RESUME-ATS.git
cd AI-RESUME-ATS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. (Optional) Configure environment for Layer E or cloud AI providers
cp backend/.env.example backend/.env
# Edit backend/.env — all fields are optional; system runs fully offline without any keys

# 4. Run end-to-end verification test
python backend/test.py

# 5. Start the web application
python backend/run.py
```
Open **`http://localhost:8000`** in your browser.

---

### Option 2: Run with Docker Compose
```bash
docker compose up --build
```
Open **`http://localhost:8000`**.

---

### Option 3: Deploy to Free Cloud (Sevalla / Render)
1. Push your code to GitHub: `swapnilsupe01/AI-RESUME-ATS`.
2. Connect your repository to **Sevalla** or **Render**.
3. Select **Docker Deployment** (or Web Service).
4. The system automatically reads `Dockerfile` or `Procfile` and boots your live URL.

---

## 8. Layer E — AI Resume Upgrade Engine: Detailed Workflow

```text
  Upload Resume PDF / Paste Text
             │
             ▼
  POST /api/upgrade/generate-suggestions  (resume + JD)
             │
     ┌───────┴─────────────────────────────┐
     ▼                                     ▼
  HF Mistral-7B-Instruct              Local RAG Engine
  (if HF_TOKEN configured)            (always available offline)
     └───────────────────┬─────────────────┘
                         │
                         ▼
             Hallucination Guard
        ┌────────────────────────────┐
        │ New metrics/numbers?       │ → 🟡 needs_confirmation
        │ New tools not on resume?   │ → 🔴 unsupported
        │ Verb/phrasing upgrade only?│ → 🟢 supported
        └────────────────────────────┘
                         │
                         ▼
          Suggestion Review Studio (UI)
      ┌───────────────────────────────────┐
      │  For each AI suggestion:          │
      │  • Accept (with optional edit)    │
      │  • Reject → keeps original text   │
      │  • Filter by status/evidence      │
      └───────────────────────────────────┘
                         │
                         ▼
      GET /api/upgrade/approved-resume
      (only accepted suggestions applied)
                         │
                         ▼
      POST /api/upgrade/export-pdf
      → ATS-compliant single-column PDF download
```

**Key Design Guarantee**: No hallucinated skills, tools, metrics, certifications, or achievements can reach the candidate's final document. Every non-trivial factual claim in an AI suggestion is flagged before the user sees it.

---

## 9. Model & Academic Stack
* **Language Models**: Sentence-BERT Siamese Network (`all-MiniLM-L6-v2`), Mistral-7B-Instruct (optional via HF Inference API).
* **Vector Metrics**: Cosine Similarity, Dense Vector Embeddings.
* **Information Extraction**: Named Skill Entity Taxonomy, Section Parsers, PyMuPDF.
* **Statistical NLP**: TF-IDF Vectorization, N-Gram Collocations (Unigram, Bigram, Trigram).
* **Backend & Web**: FastAPI, Uvicorn, Asynchronous HTTP (`httpx`), BeautifulSoup4.
* **DevOps**: Docker, Kubernetes, Jenkins, GitHub Actions, Bandit SAST, Prometheus Metrics.
* **Layer E**: Hugging Face Inference API (optional), RAG Engine (Sentence-BERT), Rule-Based NLP Heuristics, In-Memory Session Management.

---

## 10. License
This project is licensed under the MIT License.
