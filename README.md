# AI Resume ATS — Explainable Resume & Project Intelligence System

> **An AI-powered ATS that semantically matches a resume with a job description using Sentence-BERT and additionally verifies the candidate's technical claims against their public GitHub repositories and portfolio evidence.**

[![CI/CD & DevSecOps Pipeline](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions/workflows/ci.yml/badge.svg)](https://github.com/swapnilsupe01/AI-RESUME-ATS/actions)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue?logo=docker)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-HPA%20%26%20Probes-326ce5?logo=kubernetes)](https://kubernetes.io/)
[![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD%20Pipeline-D24939?logo=jenkins)](https://www.jenkins.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 1. Dual-Layer AI Intelligence Architecture

Unlike traditional ATS systems that rely solely on keyword matching or whole-document similarity, this system introduces **two distinct intelligence layers**:

```text
                                  ┌───────────────────────────┐
                                  │        Resume PDF         │
                                  └─────────────┬─────────────┘
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       ▼                                                 ▼
             Layer A: Job Matching                             Layer B: Public Evidence
        ┌─────────────────────────────┐                   ┌─────────────────────────────┐
        │       Job Description       │                   │     GitHub & Portfolios     │
        │              ↓              │                   │              ↓              │
        │   Skill-Level S-BERT Match  │                   │ Public Metadata & READMEs   │
        │              ↓              │                   │              ↓              │
        │  TF-IDF / N-Gram Similarity │                   │   Semantic Claim Verifier   │
        │              ↓              │                   │              ↓              │
        │       Job Match Score       │                   │   Project Evidence Score    │
        └──────────────┬──────────────┘                   └──────────────┬──────────────┘
                       │                                                 │
                       └────────────────────────┬────────────────────────┘
                                                ▼
                                  ┌───────────────────────────┐
                                  │   Explainable AI Report   │
                                  │  Overall Profile Score    │
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

---

## 3. Explainable Scoring Formulation

### A. Job Match Score (Layer A)
$$\text{Job Match Score} = 0.35 \cdot S_{\text{exact}} + 0.30 \cdot S_{\text{semantic}} + 0.10 \cdot \max(\text{TF-IDF}, \text{N-Gram}) + 0.10 \cdot S_{\text{experience}} + 0.05 \cdot S_{\text{section}} + 0.05 \cdot S_{\text{education}} + 0.05 \cdot S_{\text{doc-semantic}}$$

### B. Project Evidence Score (Layer B)
$$\text{Evidence Score} = 0.50 \cdot E_{\text{GitHub}} + 0.30 \cdot E_{\text{Portfolio}} + 0.20 \cdot C_{\text{Consistency}}$$

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
│       │   ├── url_extractor.py    # GitHub & Portfolio link parser
│       │   ├── github_analyzer.py  # Public GitHub API, metadata & README parser
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
