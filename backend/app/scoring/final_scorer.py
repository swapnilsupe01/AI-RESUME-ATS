"""
Final Scorer & Dual-Intelligence Synthesis Engine.
Combines:
  - Layer A: Resume ↔ Job Description Semantic Matching (Job Match Score)
  - Layer B: Resume ↔ Public Project Evidence Verification (Evidence Score)
Produces unified, explainable candidate profile intelligence.
"""
from typing import Dict, Any, List, Optional
from app.parser.resume_parser import parse_resume
from app.extraction.project_extractor import extract_projects
from app.extraction.claim_extractor import extract_all_resume_claims
from app.evidence.url_extractor import extract_project_evidence_urls
from app.evidence.github_analyzer import analyze_all_github_evidence
from app.evidence.portfolio_analyzer import analyze_all_portfolio_evidence
from app.evidence.project_verifier import verify_project_claims
from app.scoring.ats_scorer import calculate_job_match_score
from app.scoring.evidence_scorer import calculate_evidence_score
from app.recommendations.recommendation_engine import generate_dual_recommendations

async def analyze_resume_intelligence(
    resume_text: str,
    jd_text: str,
    override_github_urls: Optional[List[str]] = None,
    override_portfolio_urls: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run complete Dual-Layer Explainable Resume Intelligence System.
    """
    # 1. Structured Resume Parsing
    parsed_resume = parse_resume(resume_text)

    # Combine detected URLs with any explicit overrides
    detected_gh = parsed_resume.get("github_urls", [])
    if override_github_urls:
        detected_gh.extend(override_github_urls)

    detected_pf = parsed_resume.get("portfolio_urls", [])
    if override_portfolio_urls:
        detected_pf.extend(override_portfolio_urls)

    # 2. Layer A: Job Description Semantic Matching
    ats_report = calculate_job_match_score(resume_text, jd_text, parsed_resume)

    # 3. Layer B: Public Project Evidence Verification
    sections = parsed_resume.get("sections", {})
    projects = extract_projects(resume_text, sections.get("projects", ""))
    project_claims = extract_all_resume_claims(projects)

    # Parse and categorize evidence URLs
    all_raw_urls = detected_gh + detected_pf
    for p in projects:
        all_raw_urls.extend(p.get("urls", []))
    
    evidence_urls = extract_project_evidence_urls(resume_text, all_raw_urls)

    # Fetch public evidence
    github_evidence = await analyze_all_github_evidence(evidence_urls["github_repositories"])
    portfolio_evidence = await analyze_all_portfolio_evidence(evidence_urls["portfolio_websites"])

    # Semantic claim verification
    verification_results = verify_project_claims(
        resume_project_claims=project_claims,
        github_evidence_list=github_evidence,
        portfolio_evidence_list=portfolio_evidence
    )

    # Evidence score calculation
    has_github = len(evidence_urls["github_repositories"]) > 0 or len(evidence_urls["github_profiles"]) > 0
    has_portfolio = len(evidence_urls["portfolio_websites"]) > 0
    evidence_report = calculate_evidence_score(verification_results, has_github, has_portfolio)

    # 4. Overall Profile Score Calculation
    job_score = ats_report["job_match_score"]
    ev_score = evidence_report["evidence_score"]

    if evidence_report["is_evidence_available"]:
        # When public project evidence exists, weight Job Match 65% + Evidence 35%
        overall_profile_score = int(round(0.65 * job_score + 0.35 * ev_score))
    else:
        # Fallback to Job Match score if no project links provided
        overall_profile_score = job_score

    # 5. Dual-Track Recommendations
    recommendations = generate_dual_recommendations(ats_report, evidence_report, verification_results)

    return {
        "candidate_name": parsed_resume["candidate_name"],
        "email": parsed_resume["email"],
        "phone": parsed_resume["phone"],
        "overall_profile_score": overall_profile_score,
        
        # Layer A: Job Match Intelligence
        "job_match": {
            "score": job_score,
            "match_level": ats_report["match_level"],
            "skill_match_score": ats_report["skill_match_score"],
            "semantic_skill_score": ats_report["semantic_skill_score"],
            "document_semantic_score": ats_report["document_semantic_score"],
            "tfidf_score": ats_report["tfidf_score"],
            "ngram_score": ats_report["ngram_score"],
            "ngram_breakdown": ats_report["ngram_breakdown"],
            "experience_match_score": ats_report["experience_match_score"],
            "section_score": ats_report["section_score"],
            "education_score": ats_report["education_score"],
            "matched_skills": ats_report["matched_skills"],
            "missing_skills": ats_report["missing_skills"],
            "skill_match_details": ats_report["skill_match_details"],
            "total_jd_skills_count": ats_report["total_jd_skills_count"]
        },

        # Layer B: Public Project Evidence Intelligence
        "project_evidence": {
            "score": ev_score,
            "evidence_level": evidence_report["evidence_level"],
            "is_evidence_available": evidence_report["is_evidence_available"],
            "github_score": evidence_report["github_score"],
            "portfolio_score": evidence_report["portfolio_score"],
            "consistency_score": evidence_report["consistency_score"],
            "total_claims_analyzed": verification_results["total_claims_analyzed"],
            "verified_claims_count": verification_results["verified_claims_count"],
            "partial_claims_count": verification_results["partial_claims_count"],
            "unsupported_claims_count": verification_results["unsupported_claims_count"],
            "project_reports": verification_results["project_reports"],
            "github_repositories": verification_results["github_repositories_analyzed"],
            "portfolios": verification_results["portfolios_analyzed"],
            "inconsistencies": verification_results["inconsistencies"]
        },

        # Extracted Structure
        "parsed_data": {
            "skills": parsed_resume["extracted_skills"],
            "github_urls": detected_gh,
            "portfolio_urls": detected_pf,
            "sections_found": [k for k, v in parsed_resume["sections"].items() if v.strip()]
        },

        # Actionable Recommendations
        "recommendations": recommendations["all_recommendations"],
        "job_recommendations": recommendations["job_recommendations"],
        "evidence_recommendations": recommendations["evidence_recommendations"]
    }
