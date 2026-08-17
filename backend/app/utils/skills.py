"""
Skill database and extraction utilities for AI Resume ATS.
Preserves specialized tech terms like C++, C#, .NET, Node.js, React.js, etc.
"""
import re
from typing import List, Set

# Curated technical skills dictionary grouped conceptually
TECH_SKILLS = [
    # Programming Languages
    "python", "java", "c++", "c#", "c", "javascript", "typescript", "go", "golang",
    "rust", "ruby", "php", "swift", "kotlin", "r", "scala", "sql", "html", "css", "bash", "shell",
    
    # Web Frameworks & Libraries
    "fastapi", "flask", "django", "react", "react.js", "reactjs", "next.js", "nextjs",
    "vue", "vue.js", "angular", "express", "express.js", "node.js", "nodejs", "spring",
    "spring boot", "asp.net", ".net", "laravel", "bootstrap", "tailwind", "tailwindcss",
    
    # Machine Learning, Deep Learning & Data Science
    "machine learning", "deep learning", "artificial intelligence", "data science",
    "nlp", "natural language processing", "computer vision", "tensorflow", "pytorch",
    "keras", "scikit-learn", "sklearn", "pandas", "numpy", "scipy", "opencv",
    "nltk", "spacy", "huggingface", "transformers", "sentence-transformers", "bert",
    "llm", "langchain", "xgboost", "lightgbm", "matplotlib", "seaborn", "plotly",
    
    # Databases & Big Data
    "postgresql", "postgres", "mysql", "sqlite", "mongodb", "redis", "elasticsearch",
    "dynamodb", "oracle", "sql server", "cassandra", "neo4j", "firebase", "supabase",
    "spark", "apache spark", "hadoop", "kafka", "snowflake", "bigquery",
    
    # Cloud, DevOps & Infrastructure
    "aws", "amazon web services", "azure", "gcp", "google cloud", "google cloud platform",
    "docker", "kubernetes", "k8s", "terraform", "ansible", "jenkins", "gitlab ci",
    "github actions", "circleci", "nginx", "apache", "linux", "unix", "git", "github",
    
    # Software Engineering Practices & Architectures
    "rest api", "restful apis", "graphql", "microservices", "agile", "scrum",
    "ci/cd", "unit testing", "integration testing", "system architecture", "object-oriented programming", "oop"
]

# Alias map for standardizing variants to canonical skill names
SKILL_ALIASES = {
    "react.js": "React",
    "reactjs": "React",
    "vue.js": "Vue.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express.js": "Express.js",
    "expressjs": "Express.js",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "k8s": "Kubernetes",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "postgres": "PostgreSQL",
    "natural language processing": "NLP",
    "artificial intelligence": "AI",
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "golang": "Go",
    "restful api": "REST API",
    "restful apis": "REST API",
    "rest apis": "REST API",
}

def canonicalize_skill(skill: str) -> str:
    """Return normalized canonical title for a skill."""
    lower_s = skill.lower().strip()
    if lower_s in SKILL_ALIASES:
        return SKILL_ALIASES[lower_s]
    # Default capitalization
    words = skill.split()
    if len(words) == 1 and len(words[0]) <= 3 and words[0] not in ["sql", "aws", "gcp", "css", "php", "nlp", "llm"]:
        return skill.upper() if skill.lower() in ["sql", "aws", "gcp", "css", "php", "nlp", "llm"] else skill.capitalize()
    return " ".join(word.capitalize() for word in words)

def extract_skills(text: str) -> Set[str]:
    """
    Extract technical skills from given text string.
    Uses regex patterns to catch exact tokens, multi-word phrases, and technical symbols (C++, C#, .NET).
    """
    if not text:
        return set()

    found_skills_map = {}
    lowered_text = f" {text.lower()} "
    
    # 1. Check multi-word and single-word skills from dictionary
    for skill in TECH_SKILLS:
        pattern = r'(?<![a-zA-Z0-9#\+])' + re.escape(skill) + r'(?![a-zA-Z0-9#\+])'
        if re.search(pattern, lowered_text):
            canonical = canonicalize_skill(skill)
            found_skills_map[canonical.lower()] = canonical
            
    # 2. Check explicitly for specific tech patterns like C++, C#, .NET
    if re.search(r'\bc\+\+\b', lowered_text) or ' c++ ' in lowered_text:
        found_skills_map["c++"] = "C++"
    if re.search(r'\bc#\b', lowered_text) or ' c# ' in lowered_text:
        found_skills_map["c#"] = "C#"
    if re.search(r'\b\.net\b', lowered_text) or ' .net ' in lowered_text:
        found_skills_map[".net"] = ".NET"

    return set(found_skills_map.values())
