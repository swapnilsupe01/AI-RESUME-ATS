"""
ATS Scorer & Analysis Engine for AI Resume ATS.
Combines Skill Matching, Semantic Embeddings, N-Gram & TF-IDF Similarity, and Section Analysis.
"""
from typing import Dict, Any, List
from app.parser.resume_parser import parse_resume
from app.utils.skills import extract_skills
from app.models.tfidf_model import get_tfidf_similarity
from app.models.ngram_model import get_ngram_similarity, get_ngram_breakdowns
from app.models.embedding_model import get_embedding_similarity

def calculate_ats_score(resume_text: str, jd_text: str) -> Dict[str, Any]:
    """
    Comprehensive ATS Evaluation Engine.
    
    Weights:
        - Skill Match Score: 40%
        - Semantic Embedding Similarity: 35%
        - N-Gram / TF-IDF Similarity: 15%
        - Structural Section Match: 10%
    """
    if not resume_text or not jd_text:
        return {
            "ats_score": 0,
            "skill_match_score": 0,
            "semantic_score": 0,
            "tfidf_score": 0,
            "ngram_score": 0,
            "section_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "recommendations": ["Please provide valid Resume and Job Description content."]
        }

    # 1. Structured Parsing & Skill Extraction
    parsed_resume = parse_resume(resume_text)
    resume_skills = extract_skills(resume_text)
    jd_skills = extract_skills(jd_text)

    matched_skills = sorted(list(resume_skills.intersection(jd_skills)))
    missing_skills = sorted(list(jd_skills - resume_skills))

    if jd_skills:
        skill_match_score = float(round((len(matched_skills) / len(jd_skills)) * 100, 2))
    else:
        # Fallback if JD lists no explicit skills
        skill_match_score = 75.0 if len(matched_skills) > 0 else 50.0

    # 2. Similarity Calculations
    tfidf_score = get_tfidf_similarity(resume_text, jd_text)
    ngram_breakdowns = get_ngram_breakdowns(resume_text, jd_text)
    ngram_score = ngram_breakdowns["bigram_score"]
    embedding_score = get_embedding_similarity(resume_text, jd_text)

    # 3. Structural Section Match Score
    sections = parsed_resume["sections"]
    present_sections = [sec for sec, content in sections.items() if len(content.strip()) > 0]
    # Check key sections (Education, Experience, Projects)
    section_score = float(round((len(present_sections) / max(1, len(sections))) * 100, 2))
    if len(present_sections) == 0:
        section_score = 70.0  # Heuristic baseline if standard headings missing

    # 4. Final Weighted ATS Formula
    final_score = (
        0.40 * skill_match_score +
        0.35 * embedding_score +
        0.15 * max(tfidf_score, ngram_score) +
        0.10 * section_score
    )
    final_ats_score = int(round(max(0.0, min(100.0, final_score))))

    # 5. Dynamic Recommendations Generation
    recommendations = []
    if missing_skills:
        top_missing = missing_skills[:5]
        recommendations.append(f"Add key missing job requirements to your skills section: {', '.join(top_missing)}.")
        
    if embedding_score < 70.0:
        recommendations.append("Align your project descriptions and work experience bullet points closer to the terminology used in the job posting.")
        
    if skill_match_score < 60.0:
        recommendations.append("Highlight specific domain tools, frameworks, and technical keywords mentioned in the Job Description.")
        
    if not sections.get("projects"):
        recommendations.append("Include a dedicated 'Projects' section highlighting practical hands-on application of your technical skills.")

    if final_ats_score >= 80:
        match_level = "Excellent Match"
    elif final_ats_score >= 65:
        match_level = "Good Match"
    elif final_ats_score >= 50:
        match_level = "Moderate Match"
    else:
        match_level = "Low Match"

    return {
        "candidate_name": parsed_resume["candidate_name"],
        "email": parsed_resume["email"],
        "ats_score": final_ats_score,
        "match_level": match_level,
        "skill_match_score": skill_match_score,
        "semantic_score": embedding_score,
        "tfidf_score": tfidf_score,
        "ngram_score": ngram_score,
        "ngram_breakdown": ngram_breakdowns,
        "section_score": section_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "total_jd_skills_count": len(jd_skills),
        "recommendations": recommendations
    }
