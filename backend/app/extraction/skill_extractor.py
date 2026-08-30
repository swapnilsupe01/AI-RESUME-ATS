"""
Skill Extractor module.
Extracts categorized skills from Resume text and Job Description text.
"""
from typing import Dict, List, Set, Any
from app.utils.skills import extract_skills, normalize_skill, SKILL_CATEGORIES, ALL_SKILLS

def extract_job_skills(jd_text: str) -> Dict[str, Any]:
    """
    Extract required technical skills from Job Description, categorized by technical domain.
    """
    skills = extract_skills(jd_text)
    
    categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_CATEGORIES}
    categorized["Other Technical Skills"] = []

    for skill in sorted(list(skills)):
        assigned = False
        for cat, skill_list in SKILL_CATEGORIES.items():
            if skill in [s.lower() for s in skill_list]:
                categorized[cat].append(skill)
                assigned = True
                break
        if not assigned:
            categorized["Other Technical Skills"].append(skill)

    # Filter out empty categories
    filtered_cat = {k: v for k, v in categorized.items() if v}

    return {
        "all_skills": sorted(list(skills)),
        "categorized_skills": filtered_cat,
        "count": len(skills)
    }

def extract_resume_skills(resume_text: str) -> Dict[str, Any]:
    """
    Extract technical skills from resume with domain mapping.
    """
    skills = extract_skills(resume_text)
    
    categorized: Dict[str, List[str]] = {cat: [] for cat in SKILL_CATEGORIES}
    for skill in sorted(list(skills)):
        for cat, skill_list in SKILL_CATEGORIES.items():
            if skill in [s.lower() for s in skill_list]:
                categorized[cat].append(skill)
                break

    return {
        "all_skills": sorted(list(skills)),
        "categorized_skills": {k: v for k, v in categorized.items() if v},
        "count": len(skills)
    }
