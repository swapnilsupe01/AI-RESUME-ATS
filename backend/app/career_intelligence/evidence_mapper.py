"""
Evidence Mapper for Layer F — AI Career Intelligence Engine.
Correlates resume claims, skills, and projects with GitHub repository evidence,
commit forensics, dependency files, and live deployment artifacts.
"""

from typing import Dict, Any, List, Optional
from .claim_analyzer import ResumeClaim, EvidenceStatus


def map_claim_evidence(
    claims: List[ResumeClaim],
    github_forensics: Optional[Dict[str, Any]] = None,
    verified_certifications: Optional[List[Dict[str, Any]]] = None,
    live_projects: Optional[List[Dict[str, Any]]] = None
) -> List[ResumeClaim]:
    """
    Evaluate evidence for each resume claim using available forensic and project data.
    """
    gh_data = github_forensics or {}
    repos = gh_data.get("repositories", []) or gh_data.get("repos", [])
    gh_languages = gh_data.get("languages", {}) or {}
    gh_skills = [s.lower() for s in gh_data.get("detected_skills", [])]
    
    cert_names = [c.get("name", "").lower() for c in (verified_certifications or [])]
    live_urls = [p.get("live_url", "").lower() for p in (live_projects or []) if p.get("live_url")]

    updated_claims: List[ResumeClaim] = []

    for claim in claims:
        evidence_found: List[str] = []
        evidence_missing: List[str] = []
        status: EvidenceStatus = "insufficient_evidence"
        
        claim_skills_lower = [s.lower() for s in claim.related_skills]
        claim_text_lower = claim.text.lower()
        
        # 1. Check if source is work experience (often proprietary/internal)
        if claim.source_section == "experience":
            status = "insufficient_evidence"
            evidence_missing.append("Proprietary/company work experience cannot be verified via public repositories.")
            # If candidate holds an official certification in the relevant area
            matched_certs = [c for c in cert_names if any(s in c for s in claim_skills_lower)]
            if matched_certs:
                evidence_found.append(f"Supported by verified credential: {matched_certs[0].title()}")
                status = "partially_supported"
        else:
            # 2. Check Project evidence in GitHub repositories
            matching_repos = []
            for r in repos:
                r_name = (r.get("name") or "").lower()
                r_desc = (r.get("description") or "").lower()
                r_tech = [t.lower() for t in r.get("topics", []) + r.get("technologies", [])]
                
                # Check if repo matches project title or claim concepts
                is_name_match = claim.source_title and (claim.source_title.lower() in r_name or r_name in claim.source_title.lower())
                is_tech_match = any(s in r_tech or s in r_desc or s in r_name for s in claim_skills_lower)
                
                if is_name_match or (is_tech_match and len(claim_skills_lower) > 0):
                    matching_repos.append(r)

            if matching_repos:
                primary_repo = matching_repos[0]
                repo_title = primary_repo.get("name", "Repository")
                evidence_found.append(f"Matching public GitHub repository found: '{repo_title}'")
                
                # Check commit activity or file dependencies
                if primary_repo.get("commits_count", 0) > 5 or primary_repo.get("commit_count", 0) > 5:
                    evidence_found.append("Active commit history detected with multi-stage development.")
                
                # Check specific category indicators
                if claim.category == "cloud_deployment" and any(k in str(primary_repo).lower() for k in ["dockerfile", "compose", "workflow", "k8s"]):
                    evidence_found.append("Repository contains deployment configuration (Dockerfile / CI workflow).")
                    status = "supported_by_available_evidence"
                elif claim.category == "testing_cicd" and any(k in str(primary_repo).lower() for k in ["test", "pytest", "jest", "actions"]):
                    evidence_found.append("Test suite or GitHub Actions automation detected in repository.")
                    status = "supported_by_available_evidence"
                elif claim.category == "api_backend" and any(k in str(primary_repo).lower() for k in ["routes", "router", "app.py", "main.py", "controller"]):
                    evidence_found.append("API routing and controller architecture detected in repository.")
                    status = "supported_by_available_evidence"
                elif claim.category == "performance_optimization" and claim.metrics_claimed:
                    evidence_found.append(f"Code implementation exists in repository '{repo_title}'.")
                    evidence_missing.append(f"Specific quantitative gain ({claim.metrics_claimed}) requires recruiter interview validation of baseline telemetry.")
                    status = "partially_supported"
                else:
                    status = "supported_by_available_evidence"
            else:
                # No matching repository found
                if gh_data:
                    # Check general language overlap
                    lang_overlap = [s for s in claim_skills_lower if s in [l.lower() for l in gh_languages.keys()] or s in gh_skills]
                    if lang_overlap:
                        evidence_found.append(f"Candidate demonstrated practical use of {', '.join(lang_overlap).title()} across other public repositories.")
                        evidence_missing.append(f"Dedicated public repository for '{claim.source_title or 'this project'}' was not linked or is private.")
                        status = "partially_supported"
                    else:
                        evidence_missing.append(f"No public repository, commit logs, or code sample found matching '{claim.source_title or 'project'}'.")
                        status = "insufficient_evidence"
                else:
                    evidence_missing.append("No GitHub profile was linked or analyzed for public code verification.")
                    status = "not_checked"

            # Check if live demo URL exists
            if any(claim.source_title.lower() in u for u in live_urls):
                evidence_found.append("Live deployment URL verified for this project.")
                if status == "insufficient_evidence":
                    status = "partially_supported"

        claim.evidence_status = status
        claim.evidence_found = evidence_found
        claim.evidence_missing = evidence_missing
        updated_claims.append(claim)

    return updated_claims


def summarize_evidence_profile(claims: List[ResumeClaim]) -> Dict[str, Any]:
    """
    Generate an overall summary of claim evidence integrity for recruiter preparation.
    """
    total = len(claims)
    if total == 0:
        return {
            "total_claims": 0,
            "status_breakdown": {},
            "supported_rate": 0.0,
            "insufficient_count": 0,
            "guidance": "No explicit technical claims detected in parsed resume sections."
        }

    breakdown = {
        "supported_by_available_evidence": 0,
        "partially_supported": 0,
        "insufficient_evidence": 0,
        "conflicting_evidence": 0,
        "not_checked": 0
    }

    for c in claims:
        breakdown[c.evidence_status] = breakdown.get(c.evidence_status, 0) + 1

    supported_count = breakdown["supported_by_available_evidence"] + breakdown["partially_supported"]
    rate = round((supported_count / total) * 100, 1)

    return {
        "total_claims": total,
        "status_breakdown": breakdown,
        "supported_rate": rate,
        "insufficient_count": breakdown["insufficient_evidence"],
        "guidance": (
            "Evidence mapping checks public artifacts (GitHub repos, commit logs, live URLs, certs). "
            "Claims marked 'insufficient_evidence' are standard for proprietary employer experience or private coursework "
            "and should be probed using the Recruiter Interview Kit questions rather than penalized."
        )
    }
