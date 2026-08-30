"""
Experience & Requirements Matcher.
Analyzes education levels, years of experience indicators, and project complexity.
"""
import re
from typing import Dict, Any

EDUCATION_KEYWORDS = ["bachelor", "master", "phd", "b.tech", "m.tech", "b.e", "b.s", "computer engineering", "computer science"]

def evaluate_experience_and_education(resume_text: str, jd_text: str, sections: Dict[str, str]) -> Dict[str, Any]:
    """
    Evaluate structural sections, education background, and experience indicators.
    """
    r_lower = resume_text.lower()
    jd_lower = jd_text.lower()

    # Education match
    jd_edu_required = any(k in jd_lower for k in EDUCATION_KEYWORDS)
    resume_edu_present = any(k in r_lower for k in EDUCATION_KEYWORDS) or len(sections.get("education", "").strip()) > 10

    if jd_edu_required:
        edu_score = 100.0 if resume_edu_present else 40.0
    else:
        edu_score = 100.0 if resume_edu_present else 80.0

    # Section completeness
    present_sections = [sec for sec, content in sections.items() if len(content.strip()) > 0]
    section_score = float(round((len(present_sections) / max(1, len(sections))) * 100, 2))
    if len(present_sections) == 0:
        section_score = 70.0

    # Experience section evaluation
    exp_content = sections.get("experience", "")
    projects_content = sections.get("projects", "")
    
    if len(exp_content.strip()) > 50 or len(projects_content.strip()) > 50:
        experience_match_score = 90.0
    elif len(exp_content.strip()) > 0 or len(projects_content.strip()) > 0:
        experience_match_score = 75.0
    else:
        experience_match_score = 50.0

    return {
        "education_score": edu_score,
        "section_score": section_score,
        "experience_match_score": experience_match_score,
        "present_sections": present_sections
    }
