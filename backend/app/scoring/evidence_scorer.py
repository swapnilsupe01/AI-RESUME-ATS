"""
Evidence Scorer Engine.
Calculates Multi-Source Public Evidence Score across:
  - GitHub Project Evidence: 40%
  - LinkedIn Professional Verification: 30%
  - Portfolio Evidence: 20%
  - Resume Project Consistency: 10%
"""
from typing import Dict, Any, List

def calculate_evidence_score(
    verification_results: Dict[str, Any],
    has_github: bool,
    has_linkedin: bool,
    has_portfolio: bool
) -> Dict[str, Any]:
    """
    Calculate Evidence Score across GitHub, LinkedIn, and Portfolio sources.
    """
    if not has_github and not has_linkedin and not has_portfolio:
        return {
            "evidence_score": 0,
            "evidence_level": "No Public Evidence Linked",
            "github_score": 0.0,
            "linkedin_score": 0.0,
            "portfolio_score": 0.0,
            "consistency_score": 0.0,
            "is_evidence_available": False
        }

    overall_claim_rate = verification_results.get("overall_evidence_score", 0.0)
    inconsistencies = verification_results.get("inconsistencies", [])
    
    # 1. GitHub Score Component
    github_repos = verification_results.get("github_repositories_analyzed", [])
    gh_score = overall_claim_rate if github_repos else 0.0

    # 2. LinkedIn Score Component
    li_data = verification_results.get("linkedin_evidence")
    if li_data and li_data.get("is_accessible"):
        # Base score on verified headline, experience, and certifications
        li_score = 90.0 if li_data.get("experience") or li_data.get("certifications") else 75.0
    else:
        li_score = 0.0

    # 3. Portfolio Score Component
    portfolios = verification_results.get("portfolios_analyzed", [])
    if portfolios:
        accessible_count = sum(1 for p in portfolios if p.get("is_accessible"))
        pf_score = (accessible_count / max(1, len(portfolios))) * 85.0
    else:
        pf_score = 0.0

    # 4. Consistency Score Component
    if inconsistencies:
        consistency_score = max(20.0, 100.0 - (len(inconsistencies) * 35.0))
    else:
        consistency_score = 95.0

    # Dynamic multi-source weighting
    weights = []
    scores = []

    if has_github:
        weights.append(0.40)
        scores.append(gh_score)
    if has_linkedin:
        weights.append(0.30)
        scores.append(li_score)
    if has_portfolio:
        weights.append(0.20)
        scores.append(pf_score)
    
    weights.append(0.10)
    scores.append(consistency_score)

    total_weight = sum(weights)
    weighted_score = sum(w * s for w, s in zip(weights, scores)) / total_weight

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
        "linkedin_score": float(round(li_score, 2)),
        "portfolio_score": float(round(pf_score, 2)),
        "consistency_score": float(round(consistency_score, 2)),
        "is_evidence_available": True
    }
