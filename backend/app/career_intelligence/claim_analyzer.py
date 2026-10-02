"""
Resume Claim Analyzer for Layer F — AI Career Intelligence Engine.
Identifies and categorizes technical, architectural, performance, and leadership claims
from resume bullet points and project descriptions, preparing them for evidence mapping
and recruiter probing.
"""

import re
import uuid
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

EvidenceStatus = Literal[
    "supported_by_available_evidence",
    "partially_supported",
    "insufficient_evidence",
    "conflicting_evidence",
    "not_checked"
]

ClaimCategory = Literal[
    "api_backend",
    "architecture_scale",
    "performance_optimization",
    "cloud_deployment",
    "security_auth",
    "ml_ai_data",
    "testing_cicd",
    "database_caching",
    "leadership_ownership",
    "general_technical"
]


class ResumeClaim(BaseModel):
    claim_id: str = Field(default_factory=lambda: f"claim_{uuid.uuid4().hex[:8]}")
    text: str
    category: ClaimCategory
    source_section: str = "projects"  # "projects", "experience", "summary"
    source_title: str = ""  # Project name or Company name
    related_skills: List[str] = Field(default_factory=list)
    metrics_claimed: Optional[str] = None
    evidence_status: EvidenceStatus = "not_checked"
    evidence_found: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    probing_focus: str = ""
    suggested_probing_questions: List[str] = Field(default_factory=list)


# Regular expression patterns for claim detection
CLAIM_PATTERNS = [
    (
        "performance_optimization",
        r"\b(improv|reduc|optimiz|decreas|boost|accelerat|increas|cut|slashed)\w*\b.*?\b(\d+%\s*|\d+x\s*|\d+\s*ms|\d+\s*sec|\$[\d,]+|\d+\s*qps|\d+k|\d+m)\b",
        "Investigate baseline measurement, profiling tool used, root bottleneck, and mathematical basis of the stated percentage/metric improvement."
    ),
    (
        "api_backend",
        r"\b(rest(?:\s*api|ful)?|graphql|grpc|endpoints?|microservices?|fastapi|flask|django|express|spring\s*boot|backend|web\s*services?)\b",
        "Inquire about request validation, status codes, pagination, error handling structure, idempotency, and API versioning."
    ),
    (
        "architecture_scale",
        r"\b(architect|distributed|high\s*concurrency|scalable|microservice|event\s*driven|kafka|rabbitmq|load\s*balanc|multi\s*tenant|pub\s*sub)\b",
        "Probe system throughput, concurrency bottlenecks, message loss handling, failover mechanisms, and trade-offs made during system design."
    ),
    (
        "security_auth",
        r"\b(auth(?:entication|orization)?|jwt|oauth\d?|rbac|csrf|xss|bcrypt|encryption|tokens?|session\s*management|security|https|ssl|cors)\b",
        "Probe token storage safety (HTTP-only cookies vs LocalStorage), token expiration & refresh flow, password hashing algorithms, and vulnerability mitigation."
    ),
    (
        "cloud_deployment",
        r"\b(deploy|docker|container|kubernetes|k8s|aws|ec2|s3|lambda|gcp|azure|terraform|ci\/cd|github\s*actions|nginx|devops)\b",
        "Ask about the deployment lifecycle, Docker multi-stage builds, environment variables management, container orchestration, and continuous integration."
    ),
    (
        "ml_ai_data",
        r"\b(machine\s*learning|deep\s*learning|pytorch|tensorflow|scikit-learn|sentence-bert|bert|llm|embeddings?|vector\s*search|rag|nlp|computer\s*vision|fine\s*tun)\w*\b",
        "Probe dataset preparation, train/val/test splits, overfitting prevention, evaluation metrics (F1, BLEU, latency), and vector retrieval math."
    ),
    (
        "database_caching",
        r"\b(postgres(?:ql)?|mysql|mongodb|redis|elasticsearch|sqlite|prisma|sqlalchemy|indexing|caching|schema\s*design|query\s*optimization)\b",
        "Probe schema normalization, indexing strategies (B-Tree, GIN), cache invalidation policies (TTL, LRU), and N+1 query prevention."
    ),
    (
        "testing_cicd",
        r"\b(pytest|unittest|jest|cypress|unit\s*test|integration\s*test|coverage|mocking|tdd|ci\/cd|pipeline)\b",
        "Ask about mock vs real dependency testing, test isolation, coverage metrics, edge case identification, and automation triggers."
    ),
    (
        "leadership_ownership",
        r"\b(spearheaded|led|lead|mentored|managed|coordinated|architected\s*end-to-end|owned|collaborated\s*with)\b",
        "Probe team dynamics, division of labor, conflict resolution, technical consensus building, and individual direct code contribution."
    ),
]


def extract_claims_from_text(
    bullet_text: str,
    source_section: str = "projects",
    source_title: str = "",
    extracted_skills: Optional[List[str]] = None
) -> List[ResumeClaim]:
    """
    Analyze a single bullet point or description and extract technical claims.
    """
    clean_text = bullet_text.strip()
    if len(clean_text) < 15:
        return []

    claims: List[ResumeClaim] = []
    known_skills = [s.lower() for s in (extracted_skills or [])]

    # Find quantitative metrics
    metric_match = re.search(r"(\d+(?:\.\d+)?%|\d+x\b|\d+\s*ms\b|\d+\s*sec\b|\$[\d,]+|\d+\s*k\b|\d+\s*m\b|\d+\s*qps\b)", clean_text, re.IGNORECASE)
    metrics_str = metric_match.group(0) if metric_match else None

    # Detect skills mentioned in this bullet
    related_skills = []
    for skill in known_skills:
        if re.search(r"\b" + re.escape(skill) + r"\b", clean_text, re.IGNORECASE):
            related_skills.append(skill.title())

    for category, pattern, focus in CLAIM_PATTERNS:
        if re.search(pattern, clean_text, re.IGNORECASE):
            questions = _generate_suggested_questions(category, clean_text, metrics_str)
            claims.append(
                ResumeClaim(
                    text=clean_text,
                    category=category,  # type: ignore
                    source_section=source_section,
                    source_title=source_title,
                    related_skills=related_skills,
                    metrics_claimed=metrics_str,
                    evidence_status="not_checked",
                    probing_focus=focus,
                    suggested_probing_questions=questions
                )
            )
            # Match top 2 most specific categories per bullet
            if len(claims) >= 2:
                break

    # If no specific category matched but text has substance, classify as general_technical
    if not claims and len(clean_text) > 30 and related_skills:
        claims.append(
            ResumeClaim(
                text=clean_text,
                category="general_technical",
                source_section=source_section,
                source_title=source_title,
                related_skills=related_skills,
                metrics_claimed=metrics_str,
                evidence_status="not_checked",
                probing_focus="Examine technical implementation, trade-offs, and candidate's specific role.",
                suggested_probing_questions=[
                    f"Walk me through how you implemented '{clean_text[:60]}...'. What was your specific contribution?",
                    "What was the most challenging technical roadblock you encountered while building this, and how did you resolve it?"
                ]
            )
        )

    return claims


def _generate_suggested_questions(category: str, text: str, metrics: Optional[str]) -> List[str]:
    """Generate precise probing questions for recruiter kit based on claim category."""
    if category == "performance_optimization" and metrics:
        return [
            f"You noted achieving {metrics} improvement. How was the baseline measured before optimization?",
            "What profiling tools or telemetry did you use to pinpoint the primary bottleneck?",
            "What architectural or code trade-off (e.g. memory vs CPU) was made to achieve this gain?"
        ]
    elif category == "api_backend":
        return [
            "How did you structure error handling and status codes across your API endpoints?",
            "How do you handle request validation and sanitize inputs to prevent injection or malformed data?",
            "If an endpoint needs to return 10,000 records, how do you design pagination and streaming?"
        ]
    elif category == "architecture_scale":
        return [
            "What were the key architectural boundaries and how did services communicate?",
            "How does your architecture prevent single points of failure when traffic spikes 10x?",
            "Why did you choose this architecture over a standard monolith or simpler design?"
        ]
    elif category == "security_auth":
        return [
            "Where and how are session tokens stored and transmitted securely between client and server?",
            "How did you prevent vulnerabilities like CSRF, XSS, or unauthorized privilege escalation?",
            "What is your refresh token rotation and revocation strategy?"
        ]
    elif category == "cloud_deployment":
        return [
            "Walk me through your deployment pipeline from git push to production release.",
            "How do you manage secret keys and configuration across development and production environments?",
            "How did you optimize your container image size and build caching?"
        ]
    elif category == "ml_ai_data":
        return [
            "How did you construct your training/validation dataset and handle class imbalance or data leakage?",
            "What evaluation metrics did you track, and what were the failure cases of your model?",
            "How do you handle embedding latency and inference compute constraints in production?"
        ]
    elif category == "database_caching":
        return [
            "How did you design your database schema and indexing strategy for heavy query paths?",
            "When using caching, how do you handle cache invalidation and ensure data consistency?",
            "How do you debug and resolve slow database queries or connection pool exhaustion?"
        ]
    elif category == "testing_cicd":
        return [
            "What is your philosophy on mocking third-party dependencies versus testing against live test instances?",
            "How do you ensure tests run deterministically in CI without flaky failures?",
            "Give an example of a difficult bug caught by your automated tests before production."
        ]
    elif category == "leadership_ownership":
        return [
            "What portion of the codebase did you personally write versus reviewing or delegating?",
            "Describe a technical disagreement during this project and how you reached consensus.",
            "How did you measure the success and adoption of the features you delivered?"
        ]
    return [
        "Can you walk me through the end-to-end architecture of this project?",
        "What would you redesign if you were to rebuild this project from scratch today?"
    ]


def analyze_resume_claims(
    projects: Optional[List[Dict[str, Any]]] = None,
    experience: Optional[List[Dict[str, Any]]] = None,
    summary: str = "",
    extracted_skills: Optional[List[str]] = None
) -> List[ResumeClaim]:
    """
    Extract and structure all technical claims from a candidate's resume.
    """
    all_claims: List[ResumeClaim] = []

    # 1. Projects
    for proj in (projects or []):
        p_name = proj.get("name", "Project")
        desc = proj.get("description", "")
        if desc:
            all_claims.extend(extract_claims_from_text(desc, "projects", p_name, extracted_skills))
        for hl in proj.get("highlights", []):
            all_claims.extend(extract_claims_from_text(hl, "projects", p_name, extracted_skills))

    # 2. Work Experience
    for exp in (experience or []):
        c_name = f"{exp.get('role', 'Role')} at {exp.get('company', 'Company')}"
        for hl in exp.get("highlights", []):
            all_claims.extend(extract_claims_from_text(hl, "experience", c_name, extracted_skills))

    # 3. Summary
    if summary and len(summary) > 20:
        for sentence in summary.split(". "):
            if len(sentence.strip()) > 20:
                all_claims.extend(extract_claims_from_text(sentence, "summary", "Professional Summary", extracted_skills))

    # Deduplicate claims with identical text
    seen_texts = set()
    deduped_claims = []
    for c in all_claims:
        norm = c.text.lower().strip()
        if norm not in seen_texts:
            seen_texts.add(norm)
            deduped_claims.append(c)

    return deduped_claims
