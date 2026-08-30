"""
Skill Taxonomy & Dictionary for AI Resume ATS.
Comprehensive collection of technical skills, frameworks, tools, and domain keywords.
"""
from typing import Set, Dict, List

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "Programming Languages": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "r", "scala", "dart", "shell", "bash"
    ],
    "AI, Machine Learning & NLP": [
        "machine learning", "deep learning", "nlp", "natural language processing",
        "computer vision", "llm", "large language models", "bert", "sentence transformers",
        "transformers", "scikit-learn", "sklearn", "tensorflow", "keras", "pytorch",
        "pandas", "numpy", "scipy", "opencv", "spacy", "nltk", "hugging face", "huggingface",
        "langchain", "llama", "xgboost", "lightgbm", "gensim", "tf-idf", "embeddings",
        "vector database", "faiss", "chromadb", "pinecone", "data science", "data analysis"
    ],
    "Web & Backend Frameworks": [
        "fastapi", "flask", "django", "express", "express.js", "nodejs", "node.js",
        "react", "react.js", "next.js", "nextjs", "vue", "vue.js", "angular",
        "spring", "spring boot", "asp.net", "laravel", "graphql", "rest api", "restful api",
        "microservices", "html", "html5", "css", "css3", "tailwind", "bootstrap"
    ],
    "Databases & Storage": [
        "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis",
        "elasticsearch", "cassandra", "dynamodb", "oracle", "mariadb", "neo4j",
        "prisma", "sqlalchemy", "hibernate"
    ],
    "Cloud & DevOps": [
        "docker", "kubernetes", "k8s", "aws", "amazon web services", "azure",
        "gcp", "google cloud", "jenkins", "github actions", "gitlab ci", "ci/cd",
        "terraform", "ansible", "linux", "unix", "git", "github", "gitlab",
        "nginx", "prometheus", "grafana", "helm", "serverless", "devops", "mlops"
    ],
    "Software Engineering & Methodologies": [
        "agile", "scrum", "jira", "git", "version control", "unit testing", "pytest",
        "test driven development", "tdd", "object oriented programming", "oop",
        "data structures", "algorithms", "system design", "distributed systems"
    ]
}

# Flatten all skills into a unified set for rapid exact & normalized lookup
ALL_SKILLS: Set[str] = {skill.lower() for cat in SKILL_CATEGORIES.values() for skill in cat}

# Common skill aliases and acronym normalizations
SKILL_ALIASES: Dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "k8s": "kubernetes",
    "reactjs": "react",
    "nodejs": "node.js",
    "vuejs": "vue",
    "nextjs": "next.js",
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "natural language processing": "nlp",
    "postgres": "postgresql",
    "sentence-bert": "sentence transformers",
    "sbert": "sentence transformers"
}

def normalize_skill(skill: str) -> str:
    """Normalize skill name to standard canonical form."""
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)

def extract_skills(text: str) -> Set[str]:
    """
    Extract technical skills from text using multi-word and single-word matching.
    """
    if not text:
        return set()

    found_skills: Set[str] = set()
    cleaned_lower = f" {text.lower()} "

    # Check multi-word and single-word skills
    for skill in ALL_SKILLS:
        # Match with boundaries to prevent substring false positives
        pattern = f" {skill} "
        if pattern in cleaned_lower or f"({skill})" in cleaned_lower or f"/{skill}/" in cleaned_lower:
            found_skills.add(normalize_skill(skill))
        elif f"\n{skill}\n" in cleaned_lower or f"• {skill}" in cleaned_lower or f"- {skill}" in cleaned_lower:
            found_skills.add(normalize_skill(skill))

    return found_skills
