"""
Content-Type Classifier for Layer E AI Resume Upgrade & Suggestion Engine.

Deterministically classifies resume text snippets into appropriate categories:
  - PROJECT_DESCRIPTION
  - TECH_STACK
  - PROJECT_TITLE
  - ACHIEVEMENT
  - WORK_EXPERIENCE
  - RESPONSIBILITY
  - SKILLS
  - EDUCATION
  - CERTIFICATION
  - OTHER

Ensures technology lists, titles, and non-narrative items are never converted
into full sentence descriptions or fabricated paragraphs.
"""

import re
from typing import Optional, Set, List, Dict, Any

# Common technical terms and tools recognized across resumes
KNOWN_TECH_TOKENS = {
    "python", "javascript", "typescript", "java", "c++", "c#", "c", "go", "golang", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "dart", "html", "css", "html5", "css3",
    "react", "react.js", "reactjs", "next.js", "nextjs", "vue", "vue.js", "vuejs", "angular",
    "svelte", "node", "node.js", "nodejs", "express", "express.js", "fastapi", "flask", "django",
    "spring", "spring boot", "asp.net", ".net", "graphql", "rest", "restful", "rest api", "apis",
    "docker", "kubernetes", "k8s", "helm", "terraform", "ansible", "jenkins", "github actions",
    "gitlab ci", "ci/cd", "circleci", "argo cd", "aws", "amazon web services", "azure", "gcp",
    "google cloud", "lambda", "ec2", "s3", "ecs", "eks", "fargate", "cloudformation",
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "elasticsearch", "cassandra",
    "dynamodb", "mariadb", "neo4j", "supabase", "firebase", "prisma", "sqlalchemy", "hibernate",
    "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "scipy",
    "opencv", "huggingface", "transformers", "sentence-bert", "bert", "ollama", "llama",
    "llama 3", "llama 3.2", "llama 3.1", "mistral", "qwen", "langchain", "llamaindex", "rag",
    "spacy", "nltk", "xgboost", "lightgbm", "matplotlib", "seaborn", "plotly",
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "linux", "ubuntu", "debian",
    "bash", "shell", "powershell", "nginx", "apache", "kafka", "rabbitmq", "celery", "airflow",
    "owasp", "owasp juice shop", "burp suite", "wireshark", "metasploit", "nmap", "sonarqube",
    "snyk", "postman", "swagger", "vite", "webpack", "babel", "tailwind", "tailwindcss",
    "bootstrap", "material-ui", "shadcn", "three.js", "threejs", "d3.js", "d3"
}

# Strong action verbs that indicate a narrative sentence or responsibility
ACTION_VERBS = {
    "developed", "developing", "develop", "architected", "architecting", "architect",
    "engineered", "engineering", "engineer", "designed", "designing", "design",
    "implemented", "implementing", "implement", "built", "building", "build",
    "created", "creating", "create", "deployed", "deploying", "deploy",
    "spearheaded", "spearheading", "spearhead", "led", "leading", "lead",
    "managed", "managing", "manage", "automated", "automating", "automate",
    "streamlined", "streamlining", "streamline", "optimized", "optimizing", "optimize",
    "refactored", "refactoring", "refactor", "conducted", "conducting", "conduct",
    "analyzed", "analyzing", "analyze", "integrated", "integrating", "integrate",
    "orchestrated", "orchestrating", "orchestrate", "maintained", "maintaining", "maintain",
    "fixed", "fixing", "fix", "resolved", "resolving", "resolve", "collaborated",
    "assisted", "partnered", "authored", "wrote", "configured", "established",
    "monitored", "produced", "scaled", "transformed", "migrated"
}


def _clean_tokens(text: str) -> List[str]:
    """Split string on delimiters into trimmed non-empty tokens."""
    return [t.strip() for t in re.split(r"[,;|/•\n\t]+", text) if t.strip()]


def classify_content_type(
    text: Optional[str],
    section_context: Optional[str] = None,
    field_name: Optional[str] = None
) -> str:
    """
    Classify resume text snippet into one of the supported categories:
      - TECH_STACK
      - PROJECT_DESCRIPTION
      - PROJECT_TITLE
      - ACHIEVEMENT
      - WORK_EXPERIENCE
      - RESPONSIBILITY
      - SKILLS
      - EDUCATION
      - CERTIFICATION
      - OTHER

    Args:
        text: The raw text snippet from the user's resume.
        section_context: Optional section name (e.g. 'project', 'experience', 'skills', 'education').
        field_name: Optional field key (e.g. 'technologies', 'tech_stack', 'description', 'highlights[0]').

    Returns:
        One of the 10 supported category string literals.
    """
    if not text or not str(text).strip():
        return "OTHER"

    raw = str(text).strip()
    lower = raw.lower()

    # ── 1. Check explicit field names ─────────────────────────────────────────
    if field_name in ("technologies", "tech_stack", "tools", "skills_list"):
        return "TECH_STACK"

    if section_context == "skills" or field_name == "skills":
        return "SKILLS"

    if section_context in ("education", "academics"):
        return "EDUCATION"

    if section_context in ("certifications", "certificates", "credentials"):
        return "CERTIFICATION"

    # ── 2. Check for Explicit Prefixes ────────────────────────────────────────
    if re.match(r"^(?:tech(?:nology)?\s*stack|technologies|tools|built\s+with|stack)\s*:\s*", lower):
        return "TECH_STACK"

    if re.match(r"^(?:skills|key\s+skills|technical\s+skills|core\s+competencies|languages(?:\s*&\s*frameworks)?)\s*:\s*", lower):
        return "SKILLS"

    # ── 3. Check for Education Patterns ──────────────────────────────────────
    if re.search(r"\b(b\.?tech|b\.?e\b|bachelor|master|m\.?tech|mca|b\.?sc|bsc|diploma|polytechnic|gpa|cgpa|\b10th\b|\b12th\b|hsc|ssc|cbse|university|college\s+of\s+engineering|institute\s+of\s+technology)\b", lower):
        # If it has degree / university keywords and lacks project action verbs
        if not any(v in lower for v in ["developed", "architected", "engineered", "built", "implemented"]):
            return "EDUCATION"

    # ── 4. Check for Certification Patterns ──────────────────────────────────
    if re.search(r"\b(certified|certification|certificate|aws\s+certified|cka\b|ckad\b|pmp\b|cissp\b|comptia|coursera|udemy|license|credential)\b", lower):
        if len(raw.split()) < 20 and not any(v in lower for v in ["developed", "architected", "engineered"]):
            return "CERTIFICATION"

    # ── 5. Check for Technology Stack List ───────────────────────────────────
    # A tech stack is characterized by:
    #   - Comma / pipe / slash / bullet separated tokens
    #   - Predominantly technical tokens / names
    #   - No predicate / action verbs linking subject to object
    #   - Example: "React, FastAPI, Python, Ollama, Llama 3.2, Docker, OWASP Juice Shop"
    #   - Example: "Python, Docker, deployment, APIs"
    tokens = _clean_tokens(raw)
    words = re.findall(r"\b[A-Za-z0-9\.\+#\-]{2,}\b", raw)
    word_count = len(words)

    # Check if string has comma/pipe/slash delimiters separating short terms
    has_delimiters = bool(re.search(r"[,|/•]", raw))
    token_count = len(tokens)

    # Check for presence of action verbs
    words_lower_set = {w.lower() for w in words}
    present_action_verbs = words_lower_set.intersection(ACTION_VERBS)

    # Count known technical terms in the text
    known_tech_matches = sum(1 for t in tokens if t.lower() in KNOWN_TECH_TOKENS or any(kt in t.lower() for kt in KNOWN_TECH_TOKENS))

    # If comma-separated or tokenized with no action verbs, or >= 50% tech tokens
    if (token_count >= 2 and not present_action_verbs) or (has_delimiters and token_count >= 3 and len(present_action_verbs) <= 0):
        # Check if average token length is short (tech names are usually 1-3 words per token)
        avg_words_per_token = word_count / max(token_count, 1)
        if avg_words_per_token <= 3.5:
            return "TECH_STACK"

    if known_tech_matches >= 2 and not present_action_verbs and word_count <= 15:
        return "TECH_STACK"

    # Ambiguous tech list with lowercase words e.g., "Python, Docker, deployment, APIs"
    if has_delimiters and token_count >= 3 and not any(raw.strip().endswith(p) for p in [".", "!", "?"]) and not present_action_verbs:
        return "TECH_STACK"

    # ── 6. Check for Achievement ─────────────────────────────────────────────
    # Achievements typically feature comparative metrics, awards, or rankings
    # Example: "Improved model accuracy from 82% to 91%."
    # Example: "Won 1st place in National AI Hackathon among 150+ teams."
    has_metric_change = bool(re.search(r"(?:from\s+\d+[%$kKmM]?\s+to\s+\d+[%$kKmM]?|\bby\s+\d+[%$kKmM]?|\b\d+%\s+(?:increase|decrease|reduction|improvement|growth|boost))", lower))
    has_award = bool(re.search(r"\b(won|awarded|1st\s+place|first\s+place|finalist|top\s+\d+|hackathon|scholarship|recognized\s+as)\b", lower))
    if has_metric_change or (has_award and word_count <= 25):
        return "ACHIEVEMENT"

    # ── 7. Check for Project Title / Headline ─────────────────────────────────
    # Short title-like phrase (< 8 words, no terminal punctuation, title case or noun endings)
    # Example: "AI-Powered Vulnerability Analysis Platform"
    # Example: "Automated ISO Compliance Engine"
    title_endings = ("platform", "engine", "system", "tool", "analyzer", "scanner", "application", "dashboard", "bot", "framework", "portal", "pipeline", "service")
    if word_count <= 8 and not raw.endswith((".", "!", "?")):
        if not present_action_verbs or raw.lower().endswith(title_endings):
            return "PROJECT_TITLE"

    # ── 8. Check for Work Experience / Responsibility ────────────────────────
    # Statements about workplace responsibilities, duties, and bug fixing
    # Example: "Worked on backend APIs and fixed bugs in the application."
    # Example: "Responsible for maintaining legacy services and improving uptime."
    is_work_resp = bool(re.search(r"^(?:worked\s+on|responsible\s+for|assisted\s+in|handled|participated\s+in|supported|maintained|collaborated\s+with|fixed\s+bugs)\b", lower))
    if is_work_resp or section_context == "experience":
        if "responsible for" in lower or "assisted" in lower or "participated" in lower:
            return "RESPONSIBILITY"
        return "WORK_EXPERIENCE"

    # ── 9. Check for Project Description ─────────────────────────────────────
    # Detailed sentence or multi-sentence project narrative
    # Example: "Developed a full-stack vulnerability scanning and intelligence platform for OWASP Juice Shop."
    # Example: "Built an AI resume analyzer using Python, FastAPI, and Sentence-BERT."
    if present_action_verbs or section_context == "project" or word_count >= 8:
        return "PROJECT_DESCRIPTION"

    return "OTHER"
