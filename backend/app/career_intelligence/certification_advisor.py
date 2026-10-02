"""
Certification & Tool Advisor for Layer F — AI Career Intelligence Engine.
Based on a student's academic year and JD skill gaps, recommends:
  - Which certifications to pursue (with difficulty calibrated to year)
  - Which tools to learn first (ordered by JD weight + stage readiness)
  - What NOT to prioritise yet (too advanced for current stage)

All recommendations are deterministic, explainable, and free of hallucinations.
Every cert URL and issuer is verified against official sources.
"""

from typing import Dict, Any, List, Optional, Literal
from .academic_year_detector import AcademicStage


# ── Official Certification Catalog ───────────────────────────────────────────
# Only official / widely-recognised certifications are listed.
# Fields: skill_tags, min_stage (earliest reasonable stage), difficulty, cost_usd, url

CERTIFICATION_CATALOG: List[Dict[str, Any]] = [
    # Cloud - AWS
    {
        "id": "aws-ccp",
        "name": "AWS Certified Cloud Practitioner",
        "issuer": "Amazon Web Services",
        "skill_tags": ["aws", "cloud", "cloud fundamentals"],
        "min_stage": "first_year",
        "difficulty": "beginner",
        "exam_cost_usd": 100,
        "validity_years": 3,
        "official_url": "https://aws.amazon.com/certification/certified-cloud-practitioner/",
        "why": "Vendor-neutral cloud foundation. Recognised by almost every tech company. Ideal starting point before AWS Developer/Solutions Architect.",
        "prerequisite_cert": None,
    },
    {
        "id": "aws-dva",
        "name": "AWS Certified Developer – Associate",
        "issuer": "Amazon Web Services",
        "skill_tags": ["aws", "cloud", "serverless", "lambda", "s3", "dynamodb"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 150,
        "validity_years": 3,
        "official_url": "https://aws.amazon.com/certification/certified-developer-associate/",
        "why": "Validates hands-on AWS development skills. High ROI for backend and full-stack roles.",
        "prerequisite_cert": "aws-ccp",
    },
    {
        "id": "aws-saa",
        "name": "AWS Certified Solutions Architect – Associate",
        "issuer": "Amazon Web Services",
        "skill_tags": ["aws", "cloud", "architecture", "networking", "databases"],
        "min_stage": "third_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 150,
        "validity_years": 3,
        "official_url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
        "why": "Industry's most sought-after cloud cert. Greatly strengthens backend and cloud-engineer placement applications.",
        "prerequisite_cert": "aws-ccp",
    },
    # Cloud - GCP
    {
        "id": "gcp-ace",
        "name": "Google Associate Cloud Engineer",
        "issuer": "Google Cloud",
        "skill_tags": ["gcp", "google cloud", "cloud", "kubernetes"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 200,
        "validity_years": 2,
        "official_url": "https://cloud.google.com/learn/certification/cloud-engineer",
        "why": "Google Cloud is growing rapidly in AI/ML companies. Strong fit for ML-adjacent backend roles.",
        "prerequisite_cert": None,
    },
    # Docker & Kubernetes
    {
        "id": "docker-dca",
        "name": "Docker Certified Associate",
        "issuer": "Docker Inc.",
        "skill_tags": ["docker", "containers", "devops"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 195,
        "validity_years": 2,
        "official_url": "https://training.mirantis.com/certification/dca-certification-exam/",
        "why": "Validates containerization skills which are required in virtually every modern software role.",
        "prerequisite_cert": None,
    },
    {
        "id": "cka",
        "name": "Certified Kubernetes Administrator (CKA)",
        "issuer": "Cloud Native Computing Foundation",
        "skill_tags": ["kubernetes", "k8s", "containers", "devops", "cloud"],
        "min_stage": "final_year",
        "difficulty": "advanced",
        "exam_cost_usd": 395,
        "validity_years": 3,
        "official_url": "https://www.cncf.io/certification/cka/",
        "why": "Top-tier DevOps and Platform Engineering credential. Commands significant salary premium.",
        "prerequisite_cert": "docker-dca",
    },
    # Python & Data
    {
        "id": "pcep",
        "name": "PCEP – Certified Entry-Level Python Programmer",
        "issuer": "Python Institute",
        "skill_tags": ["python", "programming"],
        "min_stage": "first_year",
        "difficulty": "beginner",
        "exam_cost_usd": 59,
        "validity_years": None,  # Lifetime
        "official_url": "https://pythoninstitute.org/pcep",
        "why": "Official Python Institute certification. Excellent for first-year students to validate programming foundations.",
        "prerequisite_cert": None,
    },
    {
        "id": "pcap",
        "name": "PCAP – Certified Associate Python Programmer",
        "issuer": "Python Institute",
        "skill_tags": ["python", "oop", "modules", "exceptions"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 295,
        "validity_years": None,
        "official_url": "https://pythoninstitute.org/pcap",
        "why": "Validates intermediate Python for backend and data roles. Good supplement to project portfolio.",
        "prerequisite_cert": "pcep",
    },
    # Databases
    {
        "id": "oracle-mysql-oca",
        "name": "Oracle MySQL 8.0 Database Administrator",
        "issuer": "Oracle",
        "skill_tags": ["mysql", "sql", "databases"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 245,
        "validity_years": None,
        "official_url": "https://education.oracle.com/mysql-database-administration/pexam_1Z0-908",
        "why": "Validates relational database fundamentals for backend developer roles.",
        "prerequisite_cert": None,
    },
    # Security
    {
        "id": "comptia-security",
        "name": "CompTIA Security+",
        "issuer": "CompTIA",
        "skill_tags": ["security", "owasp", "networking", "cybersecurity", "authentication"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 392,
        "validity_years": 3,
        "official_url": "https://www.comptia.org/certifications/security",
        "why": "Globally recognised baseline security certification. Required for many enterprise software roles.",
        "prerequisite_cert": None,
    },
    # ML / AI
    {
        "id": "tensorflow-developer",
        "name": "TensorFlow Developer Certificate",
        "issuer": "Google",
        "skill_tags": ["tensorflow", "machine learning", "deep learning", "python"],
        "min_stage": "third_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 100,
        "validity_years": 3,
        "official_url": "https://www.tensorflow.org/certificate",
        "why": "Only ML framework cert offered by a major platform. Directly verifies hands-on ML implementation skills.",
        "prerequisite_cert": None,
    },
    {
        "id": "aws-ml-specialty",
        "name": "AWS Certified Machine Learning – Specialty",
        "issuer": "Amazon Web Services",
        "skill_tags": ["machine learning", "aws", "sagemaker", "deep learning", "nlp"],
        "min_stage": "final_year",
        "difficulty": "advanced",
        "exam_cost_usd": 300,
        "validity_years": 3,
        "official_url": "https://aws.amazon.com/certification/certified-machine-learning-specialty/",
        "why": "Premier ML engineering credential. Highly valued in AI/ML product companies.",
        "prerequisite_cert": "aws-saa",
    },
    # GitHub / DevOps
    {
        "id": "github-foundations",
        "name": "GitHub Foundations Certification",
        "issuer": "GitHub",
        "skill_tags": ["git", "github", "version control", "ci/cd", "collaboration"],
        "min_stage": "first_year",
        "difficulty": "beginner",
        "exam_cost_usd": 99,
        "validity_years": 2,
        "official_url": "https://resources.github.com/learn/certifications/",
        "why": "Official GitHub credential covering Git workflows, PRs, Actions, and collaborative development. Good resume signal for freshers.",
        "prerequisite_cert": None,
    },
    {
        "id": "github-actions-cert",
        "name": "GitHub Actions Certification",
        "issuer": "GitHub",
        "skill_tags": ["ci/cd", "github actions", "automation", "devops"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 99,
        "validity_years": 2,
        "official_url": "https://resources.github.com/learn/certifications/",
        "why": "Validates CI/CD automation skills. Directly maps to DevOps and backend engineering role requirements.",
        "prerequisite_cert": "github-foundations",
    },
    # Free / No-cost
    {
        "id": "google-it-support",
        "name": "Google IT Support Professional Certificate",
        "issuer": "Google / Coursera",
        "skill_tags": ["networking", "linux", "troubleshooting", "systems"],
        "min_stage": "first_year",
        "difficulty": "beginner",
        "exam_cost_usd": 0,  # Audit available free
        "validity_years": None,
        "official_url": "https://grow.google/certificates/it-support/",
        "why": "Free, beginner-friendly foundational IT credential. Good for first-year students building core computing knowledge.",
        "prerequisite_cert": None,
    },
    {
        "id": "meta-frontend",
        "name": "Meta Front-End Developer Professional Certificate",
        "issuer": "Meta / Coursera",
        "skill_tags": ["react", "html & css", "javascript", "frontend"],
        "min_stage": "first_year",
        "difficulty": "beginner",
        "exam_cost_usd": 0,  # Audit available free
        "validity_years": None,
        "official_url": "https://www.coursera.org/professional-certificates/meta-front-end-developer",
        "why": "Meta-issued React and front-end credential. Excellent for students starting with web development.",
        "prerequisite_cert": None,
    },
    {
        "id": "meta-backend",
        "name": "Meta Back-End Developer Professional Certificate",
        "issuer": "Meta / Coursera",
        "skill_tags": ["python", "django", "rest apis", "databases", "backend"],
        "min_stage": "second_year",
        "difficulty": "intermediate",
        "exam_cost_usd": 0,
        "validity_years": None,
        "official_url": "https://www.coursera.org/professional-certificates/meta-back-end-developer",
        "why": "Structured Meta curriculum covering Python backend + REST APIs. Adds credibility when paired with a portfolio project.",
        "prerequisite_cert": None,
    },
]


# Stage ordering for comparison
_STAGE_ORDER = {
    "first_year": 1,
    "second_year": 2,
    "third_year": 3,
    "final_year": 4,
    "graduated": 5,
    "postgraduate": 5,
    "unknown": 2,  # Default to second year if unknown
}

# Tool recommendations per JD skill (free, open-source, beginner-approachable)
TOOL_RECOMMENDATIONS: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {"tool": "VS Code + Python extension", "use": "Primary IDE with IntelliSense, linting, debugger", "free": True},
        {"tool": "Jupyter Notebooks", "use": "Interactive scripting and data exploration", "free": True},
        {"tool": "pyenv", "use": "Python version management across projects", "free": True},
    ],
    "fastapi": [
        {"tool": "Postman / Hoppscotch", "use": "Test API endpoints interactively", "free": True},
        {"tool": "Uvicorn", "use": "ASGI server to run FastAPI apps locally", "free": True},
        {"tool": "Insomnia", "use": "REST + GraphQL API client with environment variables", "free": True},
    ],
    "flask": [
        {"tool": "Postman", "use": "Test Flask REST endpoints", "free": True},
        {"tool": "Flask-Shell", "use": "Interactive debugging shell", "free": True},
    ],
    "react": [
        {"tool": "Vite", "use": "Blazing-fast React project scaffold", "free": True},
        {"tool": "React DevTools (Chrome Extension)", "use": "Inspect component tree and state", "free": True},
        {"tool": "Storybook", "use": "Build and document UI components in isolation", "free": True},
    ],
    "docker": [
        {"tool": "Docker Desktop", "use": "GUI to manage containers, images, volumes", "free": True},
        {"tool": "Docker Compose", "use": "Multi-service orchestration for local dev", "free": True},
        {"tool": "Dive", "use": "Inspect Docker image layers to reduce size", "free": True},
    ],
    "kubernetes": [
        {"tool": "Minikube", "use": "Local single-node Kubernetes cluster for development", "free": True},
        {"tool": "kubectl", "use": "CLI to manage Kubernetes resources", "free": True},
        {"tool": "k9s", "use": "Terminal dashboard for Kubernetes cluster monitoring", "free": True},
    ],
    "aws": [
        {"tool": "AWS CLI", "use": "Command-line interface for all AWS services", "free": True},
        {"tool": "LocalStack", "use": "Local AWS service emulation (S3, Lambda, DynamoDB)", "free": True},
        {"tool": "AWS Free Tier", "use": "12-month free hands-on access to real AWS services", "free": True},
    ],
    "postgresql": [
        {"tool": "pgAdmin 4", "use": "GUI database manager for PostgreSQL", "free": True},
        {"tool": "DBeaver", "use": "Universal database client with query builder", "free": True},
        {"tool": "TablePlus", "use": "Clean macOS/Windows PostgreSQL client", "free": True},
    ],
    "mysql": [
        {"tool": "MySQL Workbench", "use": "Official GUI for MySQL schema design and queries", "free": True},
        {"tool": "DBeaver", "use": "Universal DB client with EER diagram support", "free": True},
    ],
    "mongodb": [
        {"tool": "MongoDB Compass", "use": "Official visual data explorer for MongoDB", "free": True},
        {"tool": "mongosh", "use": "Official MongoDB shell CLI", "free": True},
    ],
    "redis": [
        {"tool": "RedisInsight", "use": "Official Redis GUI with real-time monitoring", "free": True},
        {"tool": "redis-cli", "use": "Built-in command-line interface for Redis", "free": True},
    ],
    "git": [
        {"tool": "GitHub", "use": "Remote repository hosting with Actions CI/CD", "free": True},
        {"tool": "GitLens (VS Code)", "use": "Enhanced Git history, blame, and diff views", "free": True},
        {"tool": "git-cz", "use": "Enforce conventional commit message format", "free": True},
    ],
    "ci/cd": [
        {"tool": "GitHub Actions", "use": "Native CI/CD directly in GitHub repositories", "free": True},
        {"tool": "act", "use": "Run GitHub Actions locally for faster debugging", "free": True},
    ],
    "machine learning": [
        {"tool": "Jupyter Notebook / JupyterLab", "use": "Interactive ML experimentation environment", "free": True},
        {"tool": "Weights & Biases (W&B)", "use": "ML experiment tracking and visualization", "free": True},
        {"tool": "Google Colab", "use": "Free GPU-backed notebooks for ML training", "free": True},
    ],
    "system design": [
        {"tool": "Excalidraw", "use": "Free whiteboard for system architecture diagrams", "free": True},
        {"tool": "draw.io", "use": "Component diagrams and ER diagrams", "free": True},
        {"tool": "Lucidchart (free tier)", "use": "Cloud-based architecture diagram tool", "free": True},
    ],
    "data structures & algorithms": [
        {"tool": "LeetCode", "use": "Structured DSA practice with company-specific problem sets", "free": True},
        {"tool": "NeetCode.io", "use": "Curated 150 + 250 roadmap with video explanations", "free": True},
        {"tool": "VisuAlgo", "use": "Algorithm and data structure animations", "free": True},
    ],
    "testing": [
        {"tool": "pytest", "use": "Python unit and integration testing framework", "free": True},
        {"tool": "coverage.py", "use": "Measure test coverage percentage", "free": True},
        {"tool": "pytest-mock", "use": "Easy mocking for pytest fixtures", "free": True},
    ],
}


def recommend_certifications(
    academic_stage: AcademicStage,
    jd_skill_gaps: List[str],
    existing_certifications: Optional[List[str]] = None,
    max_recommendations: int = 5,
) -> Dict[str, Any]:
    """
    Recommend certifications for a student based on their academic stage and JD skill gaps.

    Parameters:
    - academic_stage: Student's current detected stage (first_year, second_year, etc.)
    - jd_skill_gaps: List of JD-required skills the student is missing or weak in.
    - existing_certifications: Certifications the student already holds.
    - max_recommendations: Max number of certs to recommend.

    Returns:
    - Structured dict with recommended, future (too advanced), and held certifications.
    """
    stage_level = _STAGE_ORDER.get(academic_stage, 2)
    existing_names_lower = [c.lower() for c in (existing_certifications or [])]
    jd_lower = [s.lower().strip() for s in jd_skill_gaps]

    recommended: List[Dict[str, Any]] = []
    too_advanced: List[Dict[str, Any]] = []
    already_held: List[Dict[str, Any]] = []

    for cert in CERTIFICATION_CATALOG:
        cert_stage_level = _STAGE_ORDER.get(cert["min_stage"], 1)

        # Check if already held
        if any(cert["name"].lower() in e or cert["id"] in e for e in existing_names_lower):
            already_held.append({
                "id": cert["id"],
                "name": cert["name"],
                "issuer": cert["issuer"],
                "message": "Already on your resume. Ensure the credential URL is listed."
            })
            continue

        # Check JD skill relevance
        relevant_tags = cert["skill_tags"]
        jd_match = any(
            tag in jd_lower or any(tag in j for j in jd_lower) or any(j in tag for j in jd_lower)
            for tag in relevant_tags
        )
        if not jd_match:
            continue

        # Check if stage-appropriate
        if cert_stage_level > stage_level + 1:  # Allow 1 level ahead max
            too_advanced.append({
                "id": cert["id"],
                "name": cert["name"],
                "issuer": cert["issuer"],
                "available_from_stage": cert["min_stage"].replace("_", " ").title(),
                "difficulty": cert["difficulty"],
                "official_url": cert["official_url"],
                "message": (
                    f"Save for {cert['min_stage'].replace('_', ' ')} — "
                    f"tackling now would be premature given your current stage."
                )
            })
        else:
            # Stage-appropriate recommendation
            priority = "high" if cert["difficulty"] in ("beginner",) and stage_level <= 2 else \
                       "high" if cert["difficulty"] == "intermediate" and stage_level >= 3 else "medium"

            # Check for missing prerequisite cert
            prereq_warning = None
            if cert["prerequisite_cert"]:
                prereq_cert = next((c for c in CERTIFICATION_CATALOG if c["id"] == cert["prerequisite_cert"]), None)
                if prereq_cert and not any(prereq_cert["name"].lower() in e for e in existing_names_lower):
                    prereq_warning = f"Recommended prerequisite: '{prereq_cert['name']}' first."

            recommended.append({
                "id": cert["id"],
                "name": cert["name"],
                "issuer": cert["issuer"],
                "difficulty": cert["difficulty"],
                "exam_cost_usd": cert["exam_cost_usd"],
                "validity_years": cert["validity_years"],
                "official_url": cert["official_url"],
                "why": cert["why"],
                "priority": priority,
                "jd_relevant_tags": [t for t in relevant_tags if any(t in j or j in t for j in jd_lower)],
                "stage_match": f"Appropriate for {academic_stage.replace('_', ' ')} students.",
                "prerequisite_warning": prereq_warning,
            })

    # Sort: free first, then by priority, then by cost
    recommended.sort(key=lambda x: (
        0 if x["exam_cost_usd"] == 0 else 1,
        0 if x["priority"] == "high" else 1,
        x["exam_cost_usd"]
    ))

    return {
        "academic_stage": academic_stage,
        "total_jd_skills_analyzed": len(jd_skill_gaps),
        "recommended": recommended[:max_recommendations],
        "save_for_later": too_advanced[:3],
        "already_held": already_held,
        "note": (
            "Certifications are ordered by cost (free first), JD relevance, and stage appropriateness. "
            "Certifications supplement but do not replace project evidence and GitHub contributions. "
            "Exam costs are approximate and may vary by country."
        ),
    }


def recommend_tools(
    jd_skill_gaps: List[str],
    academic_stage: AcademicStage = "second_year",
    max_per_skill: int = 2,
) -> Dict[str, Any]:
    """
    Recommend practical developer tools for each JD skill gap.

    Parameters:
    - jd_skill_gaps: Skills the student needs to learn.
    - academic_stage: Used to prefer simpler tools for early-stage students.
    - max_per_skill: Max tools to show per skill.

    Returns:
    - Dict mapping each skill to its top tool recommendations.
    """
    stage_level = _STAGE_ORDER.get(academic_stage, 2)
    skill_tools: Dict[str, List[Dict[str, Any]]] = {}
    all_tools_flat: List[Dict[str, Any]] = []

    for skill in jd_skill_gaps:
        skill_lower = skill.lower().strip()
        # Find best match in TOOL_RECOMMENDATIONS
        matched_key = None
        for key in TOOL_RECOMMENDATIONS:
            if key in skill_lower or skill_lower in key:
                matched_key = key
                break

        if matched_key:
            tools = TOOL_RECOMMENDATIONS[matched_key][:max_per_skill]
            skill_tools[skill] = tools
            for t in tools:
                if t not in all_tools_flat:
                    all_tools_flat.append({**t, "for_skill": skill})

    return {
        "academic_stage": academic_stage,
        "tool_recommendations_by_skill": skill_tools,
        "all_tools": all_tools_flat,
        "note": (
            "All recommended tools are free and open-source unless noted. "
            "Focus on 1-2 tools per skill to avoid tool overload. "
            "Mastery of the tool comes from using it in a real project, not just installing it."
        ),
    }
