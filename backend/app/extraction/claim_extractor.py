"""
Claim Extractor: short keyword-level claims only (<= 5 words).
TECH claims = technologies; Capability claims = normalized phrases like "JWT authentication".
Whole bullets are never claims. Numbers/metrics are never claims.
"""
import re
from typing import List, Dict, Any
from app.utils.skills import extract_skills

MAX_TECH = 12
MAX_CAPABILITY = 6
MAX_WORDS = 5

_CAPABILITIES = [
    (r'real[- ]?time|websocket|socket\.?io', "Real-time updates"),
    (r'\bjwt\b|json web token', "JWT authentication"),
    (r'oauth|google sign-?in|\bsso\b', "OAuth login"),
    (r'rest(?:ful)?\s*apis?', "REST API"),
    (r'graphql', "GraphQL API"),
    (r'\bgrpc\b', "gRPC communication"),
    (r'docker|containeri[sz]', "Docker deployment"),
    (r'kubernetes|\bhelm\b|\bk8s\b', "Kubernetes deployment"),
    (r'ci/?cd|github actions|jenkins', "CI/CD pipeline"),
    (r'\bcach(?:e|ed|ing)\b', "Caching"),
    (r'unit tests?|pytest|\bjest\b|automated tests?|test suite', "Automated testing"),
    (r'serverless|\blambda\b', "Serverless functions"),
    (r'semantic|embedding|sentence[- ]?(?:bert|transformers?)|vector', "Semantic search"),
    (r'\bnli\b|entailment', "NLI verification"),
    (r'whisper|speech|transcri', "Speech transcription"),
    (r'prometheus|monitoring|alerting', "Monitoring and alerting"),
    (r'\braft\b|consensus', "Consensus algorithm"),
    (r'pdf export|generat\w+ pdf', "PDF export"),
]
_CAP_RE = [(re.compile(p, re.I), name) for p, name in _CAPABILITIES]

_DISPLAY = {
    "reactjs": "React", "react.js": "React", "react": "React",
    "nodejs": "Node.js", "node.js": "Node.js", "node": "Node.js",
    "expressjs": "Express.js", "express.js": "Express.js", "express": "Express.js",
    "mongodb": "MongoDB", "fastapi": "FastAPI", "jwt": "JWT", "postgresql": "PostgreSQL",
    "socket.io": "Socket.IO", "grpc": "gRPC", "aws": "AWS", "sql": "SQL",
    "rest api": "REST API", "rest apis": "REST API", "go": "Go",
}


def _display(tech: str) -> str:
    t = tech.strip()
    return _DISPLAY.get(t.lower(), t.title() if len(t) > 3 else t.upper())


def _bullets(project: Dict[str, Any]) -> List[str]:
    if project.get("bullets"):
        return project["bullets"]
    desc = project.get("description", "")
    return [s.strip() for s in re.split(r'\s*[•●▪◦–—]\s+', desc) if s.strip()]


def _snippet(bullets: List[str], needle: str, title: str) -> str:
    n = needle.lower()
    for b in bullets:
        if n in b.lower():
            return b[:200]
    return title


def extract_claims_from_project(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    claims: List[Dict[str, Any]] = []
    seen = set()
    bullets = _bullets(project)
    title = project.get("title", "Project")

    for tech in project.get("technologies", []):
        name = _display(tech)
        key = name.lower()
        if key in seen or len(name.split()) > MAX_WORDS:
            continue
        seen.add(key)
        claims.append({
            "claim_type": "Technology / Skill",
            "claim": name,
            "source_snippet": _snippet(bullets, tech, title),
            "category": "Skill",
        })
        if sum(c["category"] == "Skill" for c in claims) >= MAX_TECH:
            break

    cap_count = 0
    for pattern, name in _CAP_RE:
        if cap_count >= MAX_CAPABILITY:
            break
        for b in bullets:
            if pattern.search(b):
                if name.lower() not in seen:
                    seen.add(name.lower())
                    claims.append({
                        "claim_type": "Implementation Feature",
                        "claim": name,
                        "source_snippet": b[:200],
                        "category": "Feature",
                    })
                    cap_count += 1
                break
    return claims


def extract_all_resume_claims(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for proj in projects:
        out.append({
            "project_title": proj.get("title", "Project"),
            "technologies": proj.get("technologies", []),
            "claims": extract_claims_from_project(proj),
            "urls": proj.get("urls", []),
        })
    return out
