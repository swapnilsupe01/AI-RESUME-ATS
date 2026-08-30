"""
Claim Extractor module.
Deconstructs resume project descriptions into structured, verifiable technical claims
(programming languages, libraries, tools, frameworks, and architecture implementations).
"""
import re
from typing import List, Dict, Any
from app.utils.skills import extract_skills
from app.utils.text_utils import split_into_sentences

def extract_claims_from_project(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract discrete technical claims from a single project entry.
    """
    claims: List[Dict[str, Any]] = []
    desc = project.get("description", "")
    technologies = project.get("technologies", [])
    
    # 1. Add technology claims
    for tech in technologies:
        claims.append({
            "claim_type": "Technology / Skill",
            "claim": tech.title() if len(tech) > 3 else tech.upper(),
            "source_snippet": desc,
            "category": "Skill"
        })

    # 2. Add action / implementation claims from bullet points or sentences
    sentences = split_into_sentences(desc)
    for sent in sentences:
        sent_skills = extract_skills(sent)
        if sent_skills:
            claims.append({
                "claim_type": "Implementation Feature",
                "claim": sent,
                "source_snippet": sent,
                "category": "Feature"
            })

    return claims

def extract_all_resume_claims(projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract structured claim sets across all projects in the resume.
    """
    all_project_claims = []
    for proj in projects:
        proj_claims = extract_claims_from_project(proj)
        all_project_claims.append({
            "project_title": proj.get("title", "Project"),
            "technologies": proj.get("technologies", []),
            "claims": proj_claims,
            "urls": proj.get("urls", [])
        })
    return all_project_claims
