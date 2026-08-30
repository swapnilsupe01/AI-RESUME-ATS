"""
Job Match & ATS Scorer Engine.
Calculates explainable Job Compatibility Match Score using:
  - Skill Match: 35%
  - Semantic Skill Match: 30%
  - TF-IDF / N-Gram Similarity: 10%
  - Experience Match: 10%
  - Resume Structure: 5%
  - Education & Requirements: 5%
  - Overall JD Alignment: 5%
"""
from typing import Dict, Any, List
from app.parser.resume_parser import parse_resume
from app.extraction.skill_extractor import extract_job_skills, extract_resume_skills
from app.matching.skill_matcher import match_skills_comprehensive
from app.matching.semantic_matcher import compute_semantic_alignment
from app.matching.experience_matcher import evaluate_experience_and_education
from app.models.tfidf_model import get_tfidf_similarity
from app.models.ngram_model import get_ngram_similarity, get_ngram_breakdowns

def calculate_job_match_score(
    resume_text: str, 
    jd_text: str,
    parsed_resume: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Compute comprehensive Job Match ATS Score.
    """
    if not resume_text or not jd_text:
        return {
            "job_match_score": 0,
            "skill_match_score": 0,
            "semantic_skill_score": 0,
            "document_semantic_score": 0,
            "tfidf_score": 0,
            "ngram_score": 0,
            "experience_match_score": 0,
            "section_score": 0,
            "education_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "skill_match_details": []
        }

    if parsed_resume is None:
        parsed_resume = parse_resume(resume_text)

    # 1. Skill Extraction & Matching
    jd_skill_data = extract_job_skills(jd_text)
    resume_skill_data = extract_resume_skills(resume_text)

    skill_match_res = match_skills_comprehensive(
        candidate_skills=resume_skill_data["all_skills"],
        jd_skills=jd_skill_data["all_skills"]
    )

    # 2. Similarity Models (Sentence-BERT + TF-IDF + N-Gram)
    semantic_res = compute_semantic_alignment(resume_text, jd_text)
    document_semantic_score = semantic_res["semantic_score"]
    
    tfidf_score = get_tfidf_similarity(resume_text, jd_text)
    ngram_breakdowns = get_ngram_breakdowns(resume_text, jd_text)
    ngram_score = ngram_breakdowns.get("bigram_score", 0.0)

    # 3. Experience & Structure
    exp_edu_res = evaluate_experience_and_education(
        resume_text, jd_text, parsed_resume.get("sections", {})
    )

    skill_score = skill_match_res["skill_match_score"]
    semantic_skill_score = skill_match_res["semantic_skill_score"]
    ngram_tfidf_max = max(tfidf_score, ngram_score)
    exp_score = exp_edu_res["experience_match_score"]
    sec_score = exp_edu_res["section_score"]
    edu_score = exp_edu_res["education_score"]

    # 4. Weighted Job Match Formula
    weighted_job_score = (
        0.35 * skill_score +
        0.30 * semantic_skill_score +
        0.10 * ngram_tfidf_max +
        0.10 * exp_score +
        0.05 * sec_score +
        0.05 * edu_score +
        0.05 * document_semantic_score
    )

    final_job_match_score = int(round(max(0.0, min(100.0, weighted_job_score))))

    if final_job_match_score >= 80:
        match_level = "Strong Match"
    elif final_job_match_score >= 65:
        match_level = "Good Match"
    elif final_job_match_score >= 50:
        match_level = "Moderate Match"
    else:
        match_level = "Low Match"

    return {
        "job_match_score": final_job_match_score,
        "match_level": match_level,
        "skill_match_score": skill_score,
        "semantic_skill_score": semantic_skill_score,
        "document_semantic_score": document_semantic_score,
        "tfidf_score": tfidf_score,
        "ngram_score": ngram_score,
        "ngram_breakdown": ngram_breakdowns,
        "experience_match_score": exp_score,
        "section_score": sec_score,
        "education_score": edu_score,
        "matched_skills": skill_match_res["matched_skills"],
        "missing_skills": skill_match_res["missing_skills"],
        "skill_match_details": skill_match_res["skill_match_details"],
        "total_jd_skills_count": len(jd_skill_data["all_skills"]),
        "categorized_jd_skills": jd_skill_data["categorized_skills"]
    }
