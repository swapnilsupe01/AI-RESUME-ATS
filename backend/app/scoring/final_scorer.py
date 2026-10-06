"""
Final Scorer & Quad-Intelligence Synthesis Engine.
Combines:
  - Layer A: Resume <-> Job Description Semantic Matching (S-BERT, TF-IDF, N-Gram)
  - Layer B: Resume <-> Multi-Source Public Evidence (GitHub Multi-Repo + LinkedIn Profile + Portfolio)
  - Layer C: GitHub 10-Signal Identity Ownership Verification (prevents GitHub fraud/spoofing)
  - Layer D: Code Quality & Authenticity Forensics (Anti-Fork / Anti-Template / Production Rigor)
Produces unified, explainable candidate profile intelligence with contribution graph data.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from app.parser.resume_parser import parse_resume

logger = logging.getLogger(__name__)
from app.extraction.project_extractor import extract_projects
from app.extraction.claim_extractor import extract_all_resume_claims
from app.evidence.url_extractor import extract_project_evidence_urls
from app.evidence.github_analyzer import analyze_all_github_evidence
from app.evidence.linkedin_analyzer import fetch_linkedin_evidence
from app.evidence.portfolio_analyzer import analyze_all_portfolio_evidence
from app.evidence.project_verifier import verify_project_claims
from app.evidence.identity_verifier import verify_github_ownership
from app.evidence.code_quality_analyzer import audit_all_repositories_quality
from app.scoring.ats_scorer import calculate_job_match_score
from app.scoring.evidence_scorer import calculate_evidence_score
from app.recommendations.recommendation_engine import generate_dual_recommendations


def _estimate_experience_years(resume_text: str) -> Optional[int]:
    """
    Estimate total years of experience from resume text.
    Looks for year spans like '2019 - 2024', '2020–present', or phrases like '3+ years'.
    Returns None if no reliable estimate can be made.
    """
    import datetime
    current_year = datetime.datetime.now().year

    # Pattern: 'X+ years' or 'X years of experience'
    phrase_match = re.search(r'(\d{1,2})\+?\s*years?\s*(?:of\s+)?(?:experience|exp)', resume_text, re.IGNORECASE)
    if phrase_match:
        return int(phrase_match.group(1))

    # Pattern: year spans like '2019 - 2024' or '2019–Present'
    span_matches = re.findall(r'(20\d{2})\s*[-–—]\s*(20\d{2}|present|current|now)', resume_text, re.IGNORECASE)
    if span_matches:
        earliest = min(int(m[0]) for m in span_matches)
        gap = current_year - earliest
        return min(gap, 30)  # Cap at 30 years

    # Pattern: single year mentions — find the earliest 20xx year
    all_years = re.findall(r'\b(20\d{2})\b', resume_text)
    if all_years:
        earliest = min(int(y) for y in all_years)
        if earliest < current_year:
            gap = current_year - earliest
            if 1 <= gap <= 25:
                return gap

    return None

async def analyze_resume_intelligence(
    resume_text: str,
    jd_text: str,
    override_github_urls: Optional[List[str]] = None,
    override_linkedin_urls: Optional[List[str]] = None,
    override_portfolio_urls: Optional[List[str]] = None,
    additional_links: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run complete Multi-Source Explainable Resume Intelligence System.
    """
    # 1. Structured Resume Parsing
    parsed_resume = parse_resume(resume_text, additional_links=additional_links)

    # Combine detected URLs with explicit overrides safely
    detected_gh = list(parsed_resume.get("github_urls", []))
    if override_github_urls:
        for ov in override_github_urls:
            ov_clean = ov.strip()
            if not ov_clean:
                continue
            if ov_clean not in detected_gh:
                detected_gh.append(ov_clean)

    # Candidate GitHub URLs are strictly extracted from the resume and explicit per-candidate overrides.
    # We DO NOT auto-inject the local ATS admin/server token as a candidate GitHub URL.

    detected_li = list(parsed_resume.get("linkedin_urls", []))
    if override_linkedin_urls:
        detected_li.extend(override_linkedin_urls)

    detected_pf = list(parsed_resume.get("portfolio_urls", []))
    if override_portfolio_urls:
        detected_pf.extend(override_portfolio_urls)

    # 2. Layer A: Job Description Semantic Matching
    ats_report = calculate_job_match_score(resume_text, jd_text, parsed_resume)

    # Estimate experience years from resume text (used in Signal 6 — account age check)
    resume_experience_years = _estimate_experience_years(resume_text)

    # 3. Layer B: Public Project & Career Evidence Verification
    sections = parsed_resume.get("sections", {})
    projects = extract_projects(resume_text, sections.get("projects", ""))
    project_claims = extract_all_resume_claims(projects)

    # Parse and categorize evidence URLs
    all_raw_urls = detected_gh + detected_li + detected_pf
    for p in projects:
        all_raw_urls.extend(p.get("urls", []))

    evidence_urls = extract_project_evidence_urls(resume_text, all_raw_urls)

    # Determine the candidate's own GitHub username from their resume URLs.
    # This is used as a strict owner-filter inside analyze_all_github_evidence
    # to prevent another person's repos from appearing in this candidate's audit.
    _resume_gh_username: Optional[str] = None
    if evidence_urls["github_profiles"]:
        _resume_gh_username = evidence_urls["github_profiles"][0].get("owner") or None
    elif evidence_urls["github_repositories"]:
        _resume_gh_username = evidence_urls["github_repositories"][0].get("owner") or None

    # Fetch multi-source public evidence — scoped strictly to the candidate's own account
    github_resp = await analyze_all_github_evidence(
        repo_list=evidence_urls["github_repositories"],
        user_profiles=evidence_urls["github_profiles"],
        candidate_username=_resume_gh_username,
    )
    if isinstance(github_resp, dict):
        github_evidence = github_resp.get("results", [])
    else:
        github_evidence = github_resp or []

    linkedin_evidence = None
    linkedin_username = None
    linkedin_post_github_urls: List[str] = []
    if evidence_urls["linkedin_profiles"]:
        primary_li = evidence_urls["linkedin_profiles"][0].get("url")
        linkedin_username = evidence_urls["linkedin_profiles"][0].get("username")
        if primary_li:
            linkedin_evidence = await fetch_linkedin_evidence(primary_li)
            if linkedin_evidence:
                linkedin_post_github_urls = linkedin_evidence.get("post_github_urls", []) or []
    elif evidence_urls["github_profiles"] or evidence_urls["github_repositories"]:
        fallback_handle = (
            evidence_urls["github_profiles"][0].get("owner")
            if evidence_urls["github_profiles"]
            else evidence_urls["github_repositories"][0].get("owner")
        )
        if fallback_handle:
            linkedin_username = fallback_handle
            inferred_li_url = f"https://linkedin.com/in/{fallback_handle}"
            linkedin_evidence = await fetch_linkedin_evidence(inferred_li_url)
            if linkedin_evidence:
                linkedin_post_github_urls = linkedin_evidence.get("post_github_urls", []) or []

    # ── Layer C: GitHub Identity Ownership Verification ──────────────────────
    candidate_name = parsed_resume.get("candidate_name") or ""
    resume_email   = parsed_resume.get("email") or ""

    known_repos = [
        r.get("repo", "") for r in evidence_urls.get("github_repositories", [])
        if r.get("repo")
    ]

    identity_verifications: List[Dict[str, Any]] = []
    for gh_profile in evidence_urls["github_profiles"]:
        gh_owner = gh_profile.get("owner", "")
        if gh_owner:
            owner_repos = [
                r.get("repo", "") for r in evidence_urls.get("github_repositories", [])
                if r.get("owner", "").lower() == gh_owner.lower() and r.get("repo")
            ] or known_repos
            ownership = await verify_github_ownership(
                github_username=gh_owner,
                candidate_name=candidate_name,
                linkedin_username=linkedin_username,
                resume_email=resume_email,
                resume_experience_years=resume_experience_years,
                linkedin_post_github_urls=linkedin_post_github_urls,
                known_repos=owner_repos
            )
            identity_verifications.append(ownership)

    repo_owners_checked = {iv["github_username"].lower() for iv in identity_verifications}
    for gh_repo in evidence_urls["github_repositories"]:
        repo_owner = gh_repo.get("owner", "")
        if repo_owner and repo_owner.lower() not in repo_owners_checked:
            owner_repos = [
                r.get("repo", "") for r in evidence_urls.get("github_repositories", [])
                if r.get("owner", "").lower() == repo_owner.lower() and r.get("repo")
            ]
            ownership = await verify_github_ownership(
                github_username=repo_owner,
                candidate_name=candidate_name,
                linkedin_username=linkedin_username,
                resume_email=resume_email,
                resume_experience_years=resume_experience_years,
                linkedin_post_github_urls=linkedin_post_github_urls,
                known_repos=owner_repos
            )
            identity_verifications.append(ownership)
            repo_owners_checked.add(repo_owner.lower())

    primary_identity = identity_verifications[0] if identity_verifications else None
    has_ownership_mismatch = any(
        iv.get("ownership_badge") == "mismatch"
        for iv in identity_verifications
    )
    has_uncertain_ownership = any(
        iv.get("ownership_badge") in ("mismatch", "uncertain")
        for iv in identity_verifications
    )

    # ── Strict Per-Person Repository Isolation ─────────────────────────────────
    # Strip any repositories belonging to a mismatched GitHub account so another
    # person's projects NEVER appear under this candidate's Layer B or Layer D audit.
    mismatched_usernames = {
        iv.get("github_username", "").lower()
        for iv in identity_verifications
        if iv.get("ownership_badge") == "mismatch" and iv.get("github_username")
    }

    if mismatched_usernames:
        logger.warning(
            "[FinalScorer] Removing repositories from mismatched GitHub account(s) %s for candidate '%s'",
            mismatched_usernames, candidate_name
        )
        github_evidence = [
            r for r in github_evidence
            if str(r.get("owner", "")).lower() not in mismatched_usernames
        ]

    portfolio_evidence = await analyze_all_portfolio_evidence(evidence_urls["portfolio_websites"])

    # Semantic claim verification across clean, per-person evidence sources
    verification_results = verify_project_claims(
        resume_project_claims=project_claims,
        github_evidence_list=github_evidence,
        portfolio_evidence_list=portfolio_evidence,
        linkedin_evidence=linkedin_evidence
    )

    # Evidence score calculation
    has_github    = len(github_evidence) > 0
    has_linkedin  = linkedin_evidence is not None and (
        linkedin_evidence.get("is_accessible", False)
        or linkedin_evidence.get("is_pdf_verified", False)
        or linkedin_evidence.get("heuristic_score", 0) > 0
    )
    has_portfolio = len(portfolio_evidence) > 0

    evidence_report = calculate_evidence_score(
        verification_results=verification_results,
        has_github=has_github,
        has_linkedin=has_linkedin,
        has_portfolio=has_portfolio
    )

    # ── Layer D: Code Quality & Authenticity Forensics ───────────────────────
    # Anti-Fork, Commit Cadence, Commit NER Classification, Tutorial Scanner,
    # Production Engineering Standards + Isolation Forest anomaly detection
    cand_gh_username = (
        primary_identity.get("github_username")
        if primary_identity
        else (evidence_urls["github_profiles"][0].get("owner") if evidence_urls["github_profiles"] else None)
    )

    if has_ownership_mismatch:
        code_quality_report = {
            "is_available": False,
            "overall_authenticity_score": 0,
            "overall_quality_tier": "mismatch",
            "overall_quality_tier_label": "Identity Mismatch",
            "repo_audits": [],
            "contribution_graph": None,
            "layer_d_penalty_applied": True,
            "layer_d_penalty_note": (
                "Layer D Code Quality audit blocked: GitHub profile ownership mismatch detected. "
                "The audited profile and its repositories do not belong to the candidate."
            )
        }
    else:
        # Strictly isolate candidate's repositories: do not mix third-party or another person's repos
        target_cand_user = (cand_gh_username or "").lower().strip()
        filtered_repos = []
        for r in github_evidence:
            r_owner = (r.get("owner") or "").lower().strip()
            if target_cand_user:
                if r_owner == target_cand_user:
                    filtered_repos.append(r)
            else:
                filtered_repos.append(r)

        code_quality_report = await audit_all_repositories_quality(
            github_repositories=filtered_repos,
            candidate_name=candidate_name,
            candidate_username=cand_gh_username,
            candidate_email=resume_email
        )

    # Apply ownership penalty: if identity mismatch detected, reduce evidence score
    # because all the verified repos may belong to a different person.
    if has_ownership_mismatch and evidence_report.get("evidence_score", 0) > 0:
        original_ev_score = evidence_report["evidence_score"]
        evidence_report["evidence_score"] = round(original_ev_score * 0.2, 1)  # 80% penalty
        evidence_report["ownership_penalty_applied"] = True
        evidence_report["ownership_penalty_note"] = (
            "Evidence score heavily penalized: GitHub profile ownership mismatch detected. "
            "Verified projects may belong to a different person."
        )
    elif has_uncertain_ownership and evidence_report.get("evidence_score", 0) > 0:
        original_ev_score = evidence_report["evidence_score"]
        evidence_report["evidence_score"] = round(original_ev_score * 0.6, 1)  # 40% penalty
        evidence_report["ownership_penalty_applied"] = True
        evidence_report["ownership_penalty_note"] = (
            "Evidence score partially penalized: GitHub profile ownership is uncertain. "
            "Recruiter should manually verify that this GitHub account belongs to the candidate."
        )
    else:
        evidence_report["ownership_penalty_applied"] = False
        evidence_report["ownership_penalty_note"] = None

    # 4. Overall Profile Score Calculation (Quad-Layer Synthesis)
    job_score = ats_report["job_match_score"]
    ev_score = evidence_report["evidence_score"]
    layer_d_score = code_quality_report.get("overall_authenticity_score", 0)

    if evidence_report["is_evidence_available"] and code_quality_report["is_available"]:
        # Quad-layer: Job Match 45% + Evidence 30% + Code Quality 25%
        overall_profile_score = int(round(0.45 * job_score + 0.30 * ev_score + 0.25 * layer_d_score))
    elif evidence_report["is_evidence_available"]:
        overall_profile_score = int(round(0.60 * job_score + 0.40 * ev_score))
    else:
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

        # Layer B: Public Project & Career Evidence Intelligence
        "project_evidence": {
            "score": ev_score,
            "evidence_level": evidence_report["evidence_level"],
            "is_evidence_available": evidence_report["is_evidence_available"],
            "github_score": evidence_report["github_score"],
            "linkedin_score": evidence_report["linkedin_score"],
            "portfolio_score": evidence_report["portfolio_score"],
            "consistency_score": evidence_report["consistency_score"],
            "total_claims_analyzed": verification_results["total_claims_analyzed"],
            "verified_claims_count": verification_results["verified_claims_count"],
            "partial_claims_count": verification_results["partial_claims_count"],
            "unsupported_claims_count": verification_results["unsupported_claims_count"],
            "project_reports": verification_results["project_reports"],
            "github_repositories": verification_results["github_repositories_analyzed"],
            "linkedin_profile": linkedin_evidence,
            "portfolios": verification_results["portfolios_analyzed"],
            "inconsistencies": verification_results["inconsistencies"],
            "identity_verification": {
                "verifications": identity_verifications,
                "primary": primary_identity,
                "has_mismatch": has_ownership_mismatch,
                "has_uncertain": has_uncertain_ownership,
                "ownership_penalty_applied": evidence_report.get("ownership_penalty_applied", False),
                "ownership_penalty_note": evidence_report.get("ownership_penalty_note")
            }
        },

        # Layer D: Code Quality & Authenticity Forensics
        "code_quality": code_quality_report,

        # Extracted Structure
        "parsed_data": {
            "skills": parsed_resume["extracted_skills"],
            "github_urls": detected_gh,
            "linkedin_urls": detected_li,
            "portfolio_urls": detected_pf,
            "sections_found": [k for k, v in parsed_resume["sections"].items() if v.strip()]
        },

        # Actionable Recommendations
        "recommendations": recommendations["all_recommendations"],
        "job_recommendations": recommendations["job_recommendations"],
        "evidence_recommendations": recommendations["evidence_recommendations"]
    }
