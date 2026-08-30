"""
Evidence Scorer Engine.
Calculates Public Project Evidence Score using:
  - GitHub Project Evidence: 50%
  - Portfolio Evidence: 30%
  - Resume Project Consistency: 20%
"""
from typing import Dict, Any, List

def calculate_evidence_score(
    verification_results: Dict[str, Any],
    has_github: bool,
    has_portfolio: bool
) -> Dict[str, Any]:
    """
    Calculate the Evidence Score and evidence confidence level.
    """
    if not has_github and not has_portfolio:
        return {
            "evidence_score": 0,
            "evidence_level": "No Public Links Provided",
            "github_score": 0.0,
            "portfolio_score": 0.0,
            "consistency_score": 0.0,
            "is_evidence_available": False
        }

    overall_claim_rate = verification_results.get("overall_evidence_score", 0.0)
    inconsistencies = verification_results.get("inconsistencies", [])
    
    # 1. GitHub score component
    github_repos = verification_results.get("github_repositories_analyzed", [])
    if github_repos:
        # Score based on repository retrieval, README availability, and verified claims
        gh_score = overall_claim_rate
    else:
        gh_score = 0.0

    # 2. Portfolio score component
    portfolios = verification_results.get("portfolios_analyzed", [])
    if portfolios:
        accessible_count = sum(1 for p in portfolios if p.get("is_accessible"))
        pf_score = (accessible_count / max(1, len(portfolios))) * 85.0
    else:
        pf_score = 0.0

    # 3. Consistency score component (penalizes high discrepancies)
    if inconsistencies:
        consistency_score = max(20.0, 100.0 - (len(inconsistencies) * 35.0))
    else:
        consistency_score = 95.0 if (has_github or has_portfolio) else 50.0

    # Weighted calculation
    if has_github and has_portfolio:
        weighted_score = (0.50 * gh_score) + (0.30 * pf_score) + (0.20 * consistency_score)
    elif has_github:
        weighted_score = (0.75 * gh_score) + (0.25 * consistency_score)
    elif has_portfolio:
        weighted_score = (0.75 * pf_score) + (0.25 * consistency_score)
    else:
        weighted_score = 0.0

    final_evidence_score = int(round(max(0.0, min(100.0, weighted_score))))

    if final_evidence_score >= 80:
        evidence_level = "High Evidence Support"
    elif final_evidence_score >= 55:
        evidence_level = "Moderate Evidence Support"
    elif final_evidence_score > 0:
        evidence_level = "Limited Evidence Support"
    else:
        evidence_level = "No Evidence Found"

    return {
        "evidence_score": final_evidence_score,
        "evidence_level": evidence_level,
        "github_score": float(round(gh_score, 2)),
        "portfolio_score": float(round(pf_score, 2)),
        "consistency_score": float(round(consistency_score, 2)),
        "is_evidence_available": True
    }
