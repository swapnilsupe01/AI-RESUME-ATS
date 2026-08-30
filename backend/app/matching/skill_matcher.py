"""
Skill Matcher module.
Performs multi-tiered skill matching between candidate skills and job description skills:
1. Exact & normalized token matching (100%)
2. Semantic Sentence-BERT embedding similarity for synonyms/variants (e.g. FastAPI ↔ REST API, Kubernetes ↔ Containerization)
"""
from typing import List, Dict, Any, Set
from app.models.skill_embedding_model import skill_embedding_model_instance
from app.utils.skills import normalize_skill

def match_skills_comprehensive(
    candidate_skills: List[str], 
    jd_skills: List[str],
    semantic_threshold: float = 65.0
) -> Dict[str, Any]:
    """
    Evaluate candidate skills against JD skills using exact and semantic matching.
    """
    if not jd_skills:
        return {
            "matched_skills": candidate_skills[:10],
            "missing_skills": [],
            "skill_match_details": [],
            "exact_matched_count": len(candidate_skills),
            "semantic_matched_count": 0,
            "missing_count": 0,
            "skill_match_score": 85.0 if candidate_skills else 50.0,
            "semantic_skill_score": 80.0 if candidate_skills else 50.0
        }

    candidate_norm = [normalize_skill(s) for s in candidate_skills]
    jd_norm = [normalize_skill(s) for s in jd_skills]

    match_records = skill_embedding_model_instance.match_skills_semantic(
        candidate_skills=candidate_norm,
        target_skills=jd_norm,
        threshold=semantic_threshold
    )

    matched_skills = []
    missing_skills = []
    exact_count = 0
    semantic_count = 0

    for rec in match_records:
        if rec["is_matched"]:
            matched_skills.append({
                "skill": rec["target_skill"].title(),
                "match_type": rec["match_type"],
                "matched_with": rec["matched_skill"].title() if rec["matched_skill"] else "",
                "similarity": rec["similarity"]
            })
            if rec["match_type"] == "Exact":
                exact_count += 1
            else:
                semantic_count += 1
        else:
            missing_skills.append({
                "skill": rec["target_skill"].title(),
                "similarity": rec["similarity"]
            })

    total_jd = max(1, len(jd_skills))
    
    # Exact / Strict skill score
    exact_score = float(round((exact_count / total_jd) * 100, 2))
    
    # Semantic skill score giving partial credit for strong semantic matches
    semantic_total = (exact_count * 1.0) + (semantic_count * 0.85)
    semantic_skill_score = float(round((semantic_total / total_jd) * 100, 2))

    return {
        "matched_skills": [m["skill"] for m in matched_skills],
        "missing_skills": [m["skill"] for m in missing_skills],
        "skill_match_details": matched_skills + [{"skill": m["skill"], "match_type": "Missing", "similarity": m["similarity"]} for m in missing_skills],
        "exact_matched_count": exact_count,
        "semantic_matched_count": semantic_count,
        "missing_count": len(missing_skills),
        "skill_match_score": min(100.0, exact_score + (semantic_count * 15.0 / total_jd)),
        "semantic_skill_score": min(100.0, semantic_skill_score)
    }
