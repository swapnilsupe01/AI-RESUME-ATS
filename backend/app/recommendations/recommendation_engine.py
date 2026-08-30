"""
Recommendation Engine module.
Generates dual-track actionable recommendations:
  1. Job Description & ATS Optimization Recommendations
  2. Public Project Evidence & GitHub Documentation Recommendations
"""
from typing import List, Dict, Any

def generate_dual_recommendations(
    ats_data: Dict[str, Any],
    evidence_data: Dict[str, Any],
    verification_data: Dict[str, Any]
) -> Dict[str, List[str]]:
    """
    Generate structured, actionable advice across Job Match and Evidence Verification.
    """
    job_recs: List[str] = []
    evidence_recs: List[str] = []

    # 1. Job Description Alignment Recommendations
    missing = ats_data.get("missing_skills", [])
    if missing:
        top_missing = missing[:4]
        job_recs.append(
            f"Add key missing job requirements to your skills & projects: {', '.join(top_missing)}."
        )

    if ats_data.get("semantic_skill_score", 0) < 70:
        job_recs.append(
            "Align your project descriptions and work experience bullet points closer to the terminology used in the job description."
        )

    if ats_data.get("experience_match_score", 0) < 70:
        job_recs.append(
            "Highlight specific responsibilities, measurable impacts (metrics, latency, scale), and leadership roles."
        )

    if ats_data.get("section_score", 0) < 80:
        job_recs.append(
            "Ensure standard resume section headings are present (e.g. 'Skills', 'Projects', 'Experience', 'Education')."
        )

    # 2. Public Project Evidence Recommendations
    is_ev_avail = evidence_data.get("is_evidence_available", False)
    if not is_ev_avail:
        evidence_recs.append(
            "Add public GitHub repository URLs and portfolio links to your resume so technical claims can be automatically verified."
        )
    else:
        unsupported = verification_data.get("unsupported_claims_count", 0)
        inconsistencies = verification_data.get("inconsistencies", [])

        if unsupported > 0:
            evidence_recs.append(
                f"Update your public GitHub README files to explicitly document technologies, architecture diagrams, and dependencies."
            )

        if inconsistencies:
            evidence_recs.append(
                "Align your resume technical claims with the actual dependencies and code in your linked public GitHub repositories."
            )

        if evidence_data.get("evidence_score", 0) < 75:
            evidence_recs.append(
                "Include a comprehensive `requirements.txt` or `package.json` in your public repositories to establish evidence for claimed frameworks."
            )

    if not job_recs:
        job_recs.append("Excellent alignment! Your resume closely matches the target job description.")

    if not evidence_recs:
        evidence_recs.append("Outstanding project evidence! Your public GitHub repositories strongly substantiate your resume claims.")

    return {
        "job_recommendations": job_recs,
        "evidence_recommendations": evidence_recs,
        "all_recommendations": job_recs + evidence_recs
    }
