"""
Prerequisite Knowledge Graph for Layer F — AI Career Intelligence Engine.
Maps technical skills to their foundational requirements and provides DAG traversal
and topological ordering for personalized learning roadmap generation.
"""

from typing import Dict, List, Set


# Comprehensive Computer Science & Software Engineering Prerequisite DAG
PREREQUISITES: Dict[str, List[str]] = {
    # Cloud & Infrastructure
    "aws": ["cloud fundamentals", "computer networks", "linux basics", "iam basics"],
    "gcp": ["cloud fundamentals", "computer networks", "linux basics", "iam basics"],
    "azure": ["cloud fundamentals", "computer networks", "linux basics", "iam basics"],
    "docker": ["linux basics", "cli basics", "networking basics"],
    "kubernetes": ["docker", "containers", "networking basics", "yaml"],
    "terraform": ["cloud fundamentals", "networking basics", "iac concepts"],
    "ci/cd": ["git", "linux basics", "unit testing"],
    "github actions": ["git", "yaml", "ci/cd"],
    
    # Backend Frameworks
    "fastapi": ["python", "http basics", "rest apis", "asyncio basics"],
    "flask": ["python", "http basics", "rest apis"],
    "django": ["python", "http basics", "sql basics", "mvc architecture"],
    "express": ["javascript", "node.js", "http basics", "rest apis"],
    "nestjs": ["typescript", "node.js", "oop principles", "dependency injection"],
    "spring boot": ["java", "oop principles", "http basics", "rest apis", "maven/gradle"],
    "asp.net": ["c#", "oop principles", "http basics", "rest apis"],
    
    # Frontend Frameworks
    "react": ["javascript", "html & css", "es6+", "dom manipulation"],
    "next.js": ["react", "javascript", "typescript", "ssr/ssg concepts", "node.js"],
    "vue": ["javascript", "html & css", "es6+", "dom manipulation"],
    "angular": ["typescript", "javascript", "html & css", "oop principles", "rxjs"],
    "typescript": ["javascript", "static typing concepts"],
    
    # Core Programming Languages
    "python": ["programming fundamentals", "basic data structures"],
    "javascript": ["programming fundamentals", "web basics"],
    "java": ["programming fundamentals", "oop principles"],
    "c++": ["c programming", "pointers & memory", "oop principles"],
    "c": ["programming fundamentals", "memory concepts"],
    "go": ["programming fundamentals", "concurrency concepts"],
    "rust": ["programming fundamentals", "memory management", "type systems"],
    
    # Databases & Caching
    "postgresql": ["sql basics", "relational database design", "indexing"],
    "mysql": ["sql basics", "relational database design", "indexing"],
    "mongodb": ["json/bson", "nosql concepts", "database basics"],
    "redis": ["key-value storage", "caching strategies", "networking basics"],
    "elasticsearch": ["json", "inverted index concepts", "rest apis"],
    "database indexing": ["sql basics", "b-trees", "query execution plans"],
    
    # Core CS & Systems
    "data structures & algorithms": ["programming fundamentals", "time & space complexity"],
    "system design": ["http/networking", "databases", "rest apis", "caching", "load balancing"],
    "microservices": ["rest apis", "docker", "distributed systems basics", "api gateways"],
    "distributed systems": ["computer networks", "concurrency", "operating systems"],
    "graphql": ["http basics", "rest apis", "json", "type systems"],
    "websockets": ["http basics", "tcp/ip networking", "event-driven architecture"],
    "grpc": ["http/2", "protocol buffers", "networking basics"],
    
    # AI / Machine Learning
    "machine learning": ["python", "linear algebra", "statistics & probability", "calculus"],
    "deep learning": ["machine learning", "matrix calculus", "neural networks", "python"],
    "scikit-learn": ["python", "numpy", "pandas", "machine learning"],
    "pytorch": ["python", "numpy", "deep learning", "matrix operations"],
    "tensorflow": ["python", "numpy", "deep learning", "matrix operations"],
    "nlp": ["machine learning", "python", "text processing", "linear algebra"],
    "sentence-bert": ["nlp", "transformers", "pytorch", "embeddings"],
    "vector search": ["linear algebra", "embeddings", "cosine similarity", "python"],
    "rag / llm engineering": ["python", "vector search", "prompt engineering", "apis"],
    
    # Testing & Security
    "pytest": ["python", "unit testing basics"],
    "jest": ["javascript", "unit testing basics"],
    "owasp security": ["web basics", "http", "authentication principles"],
    "jwt authentication": ["http headers", "cryptography basics", "json", "rest apis"],
    "oauth2": ["http basics", "authorization concepts", "jwt authentication"],
}


def normalize_skill_name(skill: str) -> str:
    return skill.strip().lower()


def prerequisites_for(skill: str) -> List[str]:
    """Return direct prerequisites for a given skill."""
    norm = normalize_skill_name(skill)
    return PREREQUISITES.get(norm, [])


def get_all_prerequisites(skill: str) -> Set[str]:
    """Recursively collect all foundational prerequisites for a skill."""
    visited = set()
    stack = [normalize_skill_name(skill)]
    
    while stack:
        curr = stack.pop()
        direct = PREREQUISITES.get(curr, [])
        for pr in direct:
            norm_pr = normalize_skill_name(pr)
            if norm_pr not in visited and norm_pr != normalize_skill_name(skill):
                visited.add(norm_pr)
                stack.append(norm_pr)
                
    return visited


def topological_sort_skills(skills: List[str]) -> List[str]:
    """
    Sort a list of skills such that prerequisites appear before advanced topics.
    """
    skill_set = {normalize_skill_name(s): s for s in skills}
    in_degree: Dict[str, int] = {k: 0 for k in skill_set}
    adj: Dict[str, List[str]] = {k: [] for k in skill_set}
    
    for s_norm in skill_set:
        reqs = get_all_prerequisites(s_norm)
        for req in reqs:
            if req in skill_set:
                adj[req].append(s_norm)
                in_degree[s_norm] += 1
                
    queue = [k for k, deg in in_degree.items() if deg == 0]
    ordered_norms = []
    
    while queue:
        curr = queue.pop(0)
        ordered_norms.append(curr)
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    # Add any remaining nodes in case of cycles
    for k in skill_set:
        if k not in ordered_norms:
            ordered_norms.append(k)
            
    return [skill_set[k] for k in ordered_norms]
