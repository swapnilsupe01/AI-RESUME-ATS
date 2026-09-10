"""
ESCO Hierarchical Skill Taxonomy & Domain Normalizer.
Academic Foundation:
  - Paper 5: CareerBERT: Matching Resumes to ESCO Jobs in a Shared Embedding Space
    for Generic Job Recommendations (Rosenberger, Wolfrum, Weinzierl, Kraus, Zschech;
    Expert Systems with Applications, 2025).

Provides:
  1. Canonicalization: Maps messy or variantly-spelled skill tokens (e.g. 'k8s', 'sklearn',
     'fast-api') to standard ESCO skill identifiers.
  2. Hierarchical Taxonomy: Maps skills to Sub-Domains and High-Level Occupational Domains.
  3. Taxonomy Alignment: Computes candidate skill coverage across standardized industry pillars.
"""
from typing import Dict, List, Set, Any, Tuple, Optional
import re

# ── ESCO Standardized Hierarchical Taxonomy ──────────────────────────────────────────
# Root Pillar: Information and Communication Technology (ICT)
ESCO_HIERARCHY: Dict[str, Dict[str, List[str]]] = {
    "Artificial Intelligence & Data Science": {
        "Machine Learning & Modeling": [
            "machine learning", "deep learning", "neural networks", "supervised learning",
            "unsupervised learning", "reinforcement learning", "scikit-learn", "xgboost",
            "lightgbm", "catboost", "model evaluation", "cross-validation", "svm"
        ],
        "Deep Learning & Frameworks": [
            "pytorch", "tensorflow", "keras", "transformers", "hugging face",
            "cuda", "tensorboard", "torchvision"
        ],
        "Natural Language Processing (NLP)": [
            "nlp", "natural language processing", "bert", "sentence-bert", "sbert",
            "spacy", "nltk", "gensim", "latent dirichlet allocation", "lda", "topic modeling",
            "tokenization", "named entity recognition", "ner", "word2vec", "llm", "rag"
        ],
        "Explainable AI (XAI)": [
            "shap", "shapley values", "lime", "model interpretability", "feature attribution"
        ],
        "Data Engineering & Analytics": [
            "pandas", "numpy", "scipy", "sql", "postgresql", "mysql", "mongodb",
            "spark", "apache spark", "hadoop", "etl", "data pipelines", "bigquery"
        ]
    },
    "Software Architecture & Backend Engineering": {
        "Backend Frameworks": [
            "fastapi", "flask", "django", "spring boot", "node.js", "express",
            "rest api", "graphql", "microservices", "grpc"
        ],
        "Core Programming Languages": [
            "python", "java", "c++", "golang", "rust", "c#", "typescript", "javascript"
        ],
        "Database & Storage Systems": [
            "redis", "elasticsearch", "cassandra", "dynamodb", "sqlite", "orm", "sqlalchemy"
        ]
    },
    "Cloud Infrastructure & DevOps": {
        "Containerization & Orchestration": [
            "docker", "kubernetes", "helm", "containerd", "docker compose"
        ],
        "Cloud Service Platforms": [
            "aws", "amazon web services", "azure", "google cloud", "gcp"
        ],
        "CI/CD & Automation": [
            "jenkins", "github actions", "gitlab ci", "ci/cd", "continuous integration",
            "continuous deployment", "ansible", "terraform", "prometheus", "grafana"
        ]
    },
    "Frontend & UI Engineering": {
        "Web Technologies": [
            "react", "vue.js", "angular", "html5", "css3", "tailwind css", "webpack", "vite"
        ]
    }
}

# Synonyms / Aliases mapping to Canonical ESCO Concept
ESCO_SYNONYMS: Dict[str, str] = {
    "k8s": "kubernetes",
    "kube": "kubernetes",
    "sklearn": "scikit-learn",
    "tf": "tensorflow",
    "fast-api": "fastapi",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest": "rest api",
    "gcp": "google cloud",
    "amazon web services": "aws",
    "ml": "machine learning",
    "dl": "deep learning",
    "llms": "llm",
    "s-bert": "sentence-bert",
    "sbert": "sentence-bert",
    "xgboost": "xgboost",
    "light-gbm": "lightgbm",
    "ci / cd": "ci/cd",
    "cicd": "ci/cd",
    "gh actions": "github actions",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "elastic search": "elasticsearch",
    "py": "python",
    "ts": "typescript",
    "js": "javascript"
}

# Reverse lookup index: canonical_skill -> (Pillar, SubDomain)
_REVERSE_INDEX: Dict[str, Tuple[str, str]] = {}
for pillar, subdomains in ESCO_HIERARCHY.items():
    for subdomain, skills in subdomains.items():
        for skill in skills:
            _REVERSE_INDEX[skill.lower()] = (pillar, subdomain)


def canonicalize_skill(skill_raw: str) -> str:
    """
    Normalizes a skill token to its canonical ESCO concept name.
    """
    cleaned = skill_raw.strip().lower()
    cleaned = re.sub(r'[\(\)\[\]\{\}]', '', cleaned)
    return ESCO_SYNONYMS.get(cleaned, cleaned)


def map_skills_to_esco_taxonomy(skills: List[str]) -> Dict[str, Any]:
    """
    Maps a list of raw skills extracted from a resume or job description
    into structured ESCO occupational pillars and sub-domains.

    Returns:
      {
        "canonical_skills": List[str],
        "domain_distribution": Dict[str, int],  # Count of skills per high-level pillar
        "subdomain_distribution": Dict[str, int],
        "primary_pillar": str,
        "taxonomy_coverage_ratio": float,      # Ratio of skills successfully mapped into ESCO
        "hierarchy_tree": Dict[str, Dict[str, List[str]]]  # Matched skills organized by tree
      }
    """
    canonical_set: Set[str] = set()
    for s in skills:
        if not s:
            continue
        c = canonicalize_skill(s)
        canonical_set.add(c)

    domain_counts: Dict[str, int] = {}
    subdomain_counts: Dict[str, int] = {}
    hierarchy_tree: Dict[str, Dict[str, List[str]]] = {}
    mapped_count = 0

    for c_skill in canonical_set:
        if c_skill in _REVERSE_INDEX:
            pillar, subdomain = _REVERSE_INDEX[c_skill]
            mapped_count += 1
            domain_counts[pillar] = domain_counts.get(pillar, 0) + 1
            subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1

            if pillar not in hierarchy_tree:
                hierarchy_tree[pillar] = {}
            if subdomain not in hierarchy_tree[pillar]:
                hierarchy_tree[pillar][subdomain] = []
            hierarchy_tree[pillar][subdomain].append(c_skill)

    total_skills = len(canonical_set)
    coverage = round(mapped_count / max(1, total_skills), 3)

    primary_pillar = max(domain_counts.items(), key=lambda x: x[1])[0] if domain_counts else "General Technology"

    return {
        "canonical_skills": sorted(list(canonical_set)),
        "domain_distribution": domain_counts,
        "subdomain_distribution": subdomain_counts,
        "primary_pillar": primary_pillar,
        "taxonomy_coverage_ratio": coverage,
        "hierarchy_tree": hierarchy_tree
    }


def compare_esco_taxonomy_alignment(
    resume_skills: List[str],
    jd_skills: List[str]
) -> Dict[str, Any]:
    """
    Compares the ESCO taxonomy profile of a candidate against a job vacancy.
    Shows pillar alignment and identifies taxonomy sub-domain gaps.
    """
    res_esco = map_skills_to_esco_taxonomy(resume_skills)
    jd_esco = map_skills_to_esco_taxonomy(jd_skills)

    # Calculate domain coverage (how many of JD's required pillars does candidate touch)
    jd_pillars = set(jd_esco["domain_distribution"].keys())
    res_pillars = set(res_esco["domain_distribution"].keys())

    common_pillars = jd_pillars.intersection(res_pillars)
    pillar_overlap_ratio = round(len(common_pillars) / max(1, len(jd_pillars)), 3)

    # Sub-domain gaps
    jd_subdomains = set(jd_esco["subdomain_distribution"].keys())
    res_subdomains = set(res_esco["subdomain_distribution"].keys())
    missing_subdomains = sorted(list(jd_subdomains - res_subdomains))

    return {
        "candidate_primary_pillar": res_esco["primary_pillar"],
        "vacancy_primary_pillar": jd_esco["primary_pillar"],
        "pillar_alignment_ratio": pillar_overlap_ratio,
        "matched_pillars": sorted(list(common_pillars)),
        "missing_subdomains": missing_subdomains,
        "candidate_tree": res_esco["hierarchy_tree"],
        "vacancy_tree": jd_esco["hierarchy_tree"]
    }
