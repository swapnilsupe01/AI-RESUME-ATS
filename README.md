# AI Resume ATS — Explainable Resume, Project, Identity & Code Forensics System

> **A Quad-Layer AI-powered ATS that semantically matches a resume with a job description using Sentence-BERT, verifies technical claims against public GitHub/LinkedIn evidence, defends against candidate fraud using a 10-signal GitHub ownership engine, and audits codebase originality using 5-dimension code quality forensics (anti-fork / anti-template).**

[![CI/CD & DevSecOps Pipeline](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions/workflows/ci.yml/badge.svg)](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue?logo=docker)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-HPA%20%26%20Probes-326ce5?logo=kubernetes)](https://kubernetes.io/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD%20Pipeline-D24939?logo=jenkins)](https://www.jenkins.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Quad-Layer AI Intelligence Architecture

Unlike traditional ATS systems that rely solely on keyword matching or naive whole-document similarity, this system introduces **four distinct, concurrent intelligence layers**:

```text
                                        ┌───────────────────────────┐
                                        │        Resume PDF         │
                                        └─────────────┬─────────────┘
                                                      │
         ┌──────────────────────────────┬─────────────┴─────────────┬──────────────────────────────┐
         ▼                              ▼                           ▼                              ▼
Layer A: Job Matching          Layer B: Public Evidence    Layer C: Identity & Fraud      Layer D: Code Forensics
┌─────────────────────────┐    ┌─────────────────────────┐ ┌─────────────────────────┐    ┌─────────────────────────┐
│     Job Description     │    │   GitHub & Portfolios   │ │   Anti-Spoofing Engine  │    │ Anti-Fork / Anti-Temp.  │
│            ↓            │    │            ↓            │ │            ↓            │    │            ↓            │
│ Skill-Level S-BERT Match│    │Public Metadata & READMEs│ │ 10 Multi-Source Signals │    │ 5 Forensic Dimensions   │
│            ↓            │    │            ↓            │ │            ↓            │    │            ↓            │
│TF-IDF / N-Gram Analys.  │    │ Semantic Claim Verifier │ │Commits, Posts, Bio Links│    │Commit Cadence, NER, CI  │
│            ↓            │    │            ↓            │ │            ↓            │    │            ↓            │
│     Job Match Score     │    │ Project Evidence Score  │ │ Ownership Trust Verdict │    │ Authenticity Score & T. │
└────────────┬────────────┘    └────────────┬────────────┘ └────────────┬────────────┘    └────────────┬────────────┘
             │                              │                           │                              │
             └──────────────────────────────┴─────────────┬─────────────┴──────────────────────────────┘
                                                          ▼
                                            ┌───────────────────────────┐
                                            │   Explainable AI Report   │
                                            │  Quad Overall Score (100) │
                                            │ Anti-Fraud & Quality Badg.│
                                            └───────────────────────────┘
```

---

## 2. Core Features

### 🔹 Layer A — Resume ↔ Job Description Semantic Matching
* **Skill-Level Semantic Matching**: Evaluates each required skill individually using **Sentence-BERT (`all-MiniLM-L6-v2`)** and cosine similarity matrix. Catches semantic equivalencies (e.g. *"FastAPI"* $\leftrightarrow$ *"REST API development"*).
* **Multi-Model Breakdown**: Computes Unigram, Bigram, Trigram N-gram overlaps and TF-IDF metrics.
* **Structured Section & Experience Evaluation**: Assesses education requirements, work history, and section completeness.

### 🔹 Layer B — Resume ↔ Public Project Evidence Verification
* **Automatic URL Detection**: Extracts public GitHub repository links and portfolio URLs directly from the resume text.
* **Public Project Evidence Retrieval**: Queries public repository metadata, languages, dependency files (`requirements.txt`, `package.json`), topics, and README documentation via GitHub public REST APIs.
* **Claim Extraction**: Deconstructs resume project descriptions into discrete technical claims.
* **3-Tier Evidence Confidence Categorization**:
  * 🟢 **Verified** ($\text{Cosine Similarity} \ge 80\%$): Direct code, metadata, or explicit documentation substantiates the claim.
  * 🟡 **Partially Supported** ($60\% - 79\%$): Related technologies or context exist without direct proof.
  * 🔴 **Not Supported** ($< 60\%$): Little or no evidence found in retrieved public documentation.
* **Discrepancy / Inconsistency Warnings**: Non-accusatory alerts if public code repository dependencies diverge significantly from resume claims.

### 🔹 Layer C — 10-Signal Recruiter-Side GitHub Identity Fraud Intelligence
Protects recruiters from candidate fraud where random or stolen GitHub repository URLs are pasted into a resume (e.g. candidate *Swapnil Supe* pasting an unrelated user's GitHub *swapnil-23*):
1. **GitHub Bio Display Name Match** (18%): Token overlap between GitHub profile name and candidate name.
2. **Username Name Token Overlap** (8%): Fuzzy and substring token overlap between GitHub handle and candidate name.
3. **LinkedIn Cross-Link in GitHub Bio** (18%): Validates whether the GitHub profile bio/blog explicitly points to the candidate's LinkedIn URL.
4. **Git Commit Author Names** (14%): Audits local author signatures in recent Git commits against candidate name.
5. **Public Profile Email Match** (2%): Compares public GitHub profile email with resume contact email.
6. **Account Age vs. Claimed Experience** (10%): Flags discrepancies where a candidate claims 5+ years of senior experience on an account created weeks ago.
7. **Git Commit Author Email Cross-Match** (10%): Scans raw Git commit email headers against resume contact email.
8. **Contribution History Authenticity** (5%): Audits public repository volume, follower counts, and multi-year activity graphs.
9. **Profile README Identity Scan** (5%): Extracts introductory markdown headers (`# Hi, I'm Swapnil`) from `github.com/{user}/{user}/README.md`.
10. **LinkedIn Post → GitHub Cross-Reference** (10%): Analyzes public LinkedIn technical posts to verify if the candidate publicly shared and claimed ownership of the exact GitHub repositories.
* **Ownership Trust Verdict**: Categorized into 🟢 *Ownership Confirmed*, 🟡 *Likely Owner*, 🟠 *Uncertain Ownership*, or 🔴 *Ownership Mismatch (Potential Fraud)* with automatic score penalties for suspicious accounts.

### 🔹 Layer D — 5-Dimension Code Quality & Authenticity Forensics
Answers the critical recruiter question: *"Did this candidate actually write this software, or did they fork someone else's repo, copy a YouTube tutorial, or push a single-commit ZIP dump?"*
1. **Fork & Upstream Origin Check** (25%): Inspects `repo.fork`, parent metadata, and root commit author to catch derivative clones.
2. **Commit Timeline Cadence & Anomaly Model** (25%): Uses unsupervised **Isolation Forest** scoring on commit intervals. Differentiates single-day ZIP dumps from organic multi-week development.
3. **Commit Message Semantic Quality (NER)** (15%): Categorizes commit tags using NLP token classification (`feat`, `fix`, `refactor`, `docs`, `test`) vs lazy placeholders (`update`, `done`).
4. **Tutorial & Boilerplate Fingerprint Scanner** (20%): Regex-scans repo metadata, topics, and READMEs for YouTube, Udemy, Coursera, or FreeCodeCamp starter kit markers.
5. **Production Engineering Rigor** (15%): Audits repository tree for unit tests (`pytest`, `jest`), Docker containerization (`Dockerfile`, `docker-compose`), and CI/CD pipelines (`.github/workflows`, `Jenkinsfile`).
* **Interactive Contribution Graph**: Generates a yearly commit distribution chart with clickable drill-down inspection for recruiters.

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
│       │   └── routes.py           # /api/analyze, /api/verify-project, /api/health
│       ├── parser/
│       │   ├── pdf_parser.py       # PyMuPDF text & structure extractor
│       │   └── resume_parser.py    # Contact, links & section segmentation
│       ├── extraction/
│       │   ├── skill_extractor.py  # Categorized skill taxonomy extractor
│       │   ├── project_extractor.py# Project block & repo link parser
│       │   └── claim_extractor.py  # Verifiable claim deconstructor
│       ├── evidence/
│       │   ├── url_extractor.py    # GitHub, LinkedIn & Portfolio link parser
│       │   ├── github_analyzer.py  # Public GitHub API, metadata & README parser
│       │   ├── linkedin_analyzer.py# Public LinkedIn profile, activity & post parser
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
│       └── static/
│           ├── index.html          # Dual-intelligence web UI
│           ├── style.css           # Modern dark glassmorphism theme
│           └── app.js              # Dual gauge animations & table rendering
├── dataset/
│   ├── generate_sample_pdf.py      # Sample resume PDF generator
│   ├── job_descriptions/
│   └── resumes/
└── tests/
    ├── test_parser.py
    ├── test_matching.py
    ├── test_evidence.py
    └── test_scoring.py
```

---

## 6. Quickstart & Installation

### Option 1: Run with Python Locally
```bash
# 1. Clone repository
git clone https://github.com/swapnilsupe01/AI-RESUME-ATS.git
cd AI-RESUME-ATS

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Run end-to-end verification test
python backend/test.py

# 4. Start the web application
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

## 7. Model & Academic Stack
* **Language Models**: Sentence-BERT Siamese Network (`all-MiniLM-L6-v2`).
* **Vector Metrics**: Cosine Similarity, Dense Vector Embeddings.
* **Information Extraction**: Named Skill Entity Taxonomy, Section Parsers, PyMuPDF.
* **Statistical NLP**: TF-IDF Vectorization, N-Gram Collocations (Unigram, Bigram, Trigram).
* **Backend & Web**: FastAPI, Uvicorn, Asynchronous HTTP (`httpx`), BeautifulSoup4.
* **DevOps**: Docker, Kubernetes, Jenkins, GitHub Actions, Bandit SAST, Prometheus Metrics.

---

## 8. License
This project is licensed under the MIT License.
