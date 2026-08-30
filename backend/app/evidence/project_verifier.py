"""
Project Evidence Verifier Engine.
Performs semantic claim-by-claim verification between Resume Claims and Public Evidence (GitHub / Portfolio)
using Sentence-BERT embeddings and Cosine Similarity.
Categorizes claims into 3 confidence tiers:
  🟢 Verified (Similarity >= 80%)
  🟡 Partially Supported (Similarity 60% - 79%)
  🔴 Not Supported by retrieved public evidence (Similarity < 60%)
Also flags project-evidence discrepancies and inconsistencies.
"""
from typing import List, Dict, Any, Tuple
from app.models.skill_embedding_model import skill_embedding_model_instance
from app.utils.skills import normalize_skill

def verify_project_claims(
    resume_project_claims: List[Dict[str, Any]],
    github_evidence_list: List[Dict[str, Any]],
    portfolio_evidence_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Verify all resume claims against public evidence sources.
    """
    # Consolidate all evidence snippets and technologies
    all_evidence_snippets: List[str] = []
    all_evidence_technologies: Set[str] = set()

    for gh in github_evidence_list:
        all_evidence_snippets.extend(gh.get("evidence_snippets", []))
        all_evidence_snippets.append(gh.get("description", ""))
        all_evidence_snippets.append(gh.get("readme_preview", ""))
        for t in gh.get("technologies", []):
            all_evidence_technologies.add(normalize_skill(t))
        for l in gh.get("languages", []):
            all_evidence_technologies.add(normalize_skill(l))

    for pf in portfolio_evidence_list:
        all_evidence_snippets.extend(pf.get("evidence_snippets", []))
        all_evidence_snippets.append(pf.get("preview", ""))
        for t in pf.get("technologies", []):
            all_evidence_technologies.add(normalize_skill(t))

    all_evidence_snippets = [s for s in all_evidence_snippets if s and len(s.strip()) > 3]

    project_reports: List[Dict[str, Any]] = []
    total_claims_count = 0
    verified_claims_count = 0
    partial_claims_count = 0
    unsupported_claims_count = 0
    inconsistencies: List[Dict[str, Any]] = []

    for proj in resume_project_claims:
        proj_title = proj.get("project_title", "Project")
        claims = proj.get("claims", [])
        verified_items = []
        
        # Check for matching repository for this specific project
        specific_repo_evidence = None
        for gh in github_evidence_list:
            if (gh.get("repo_name", "").lower() in proj_title.lower() or 
                proj_title.lower() in gh.get("repo_name", "").lower() or
                proj_title.lower().replace(" ", "-") in gh.get("full_name", "").lower()):
                specific_repo_evidence = gh
                break

        # Evidence pool for this project (prefer project-specific repo if found, else global pool)
        if specific_repo_evidence:
            pool_snippets = specific_repo_evidence.get("evidence_snippets", []) + [
                specific_repo_evidence.get("description", ""),
                specific_repo_evidence.get("readme_preview", "")
            ]
            pool_tech = {normalize_skill(t) for t in specific_repo_evidence.get("technologies", [])}
            repo_matched = specific_repo_evidence.get("full_name")
        else:
            pool_snippets = all_evidence_snippets
            pool_tech = all_evidence_technologies
            repo_matched = None

        proj_verified = 0
        proj_partial = 0
        proj_unsupported = 0

        for item in claims:
            total_claims_count += 1
            claim_text = item.get("claim", "")
            claim_type = item.get("claim_type", "Technology / Skill")
            
            # Exact technology presence check
            norm_claim = normalize_skill(claim_text)
            if norm_claim in pool_tech or norm_claim in [normalize_skill(s) for s in pool_snippets]:
                sim_score = 100.0
                best_evidence = f"Found in public project metadata ({claim_text})"
                status = "Verified"
                badge = "verified"
                proj_verified += 1
                verified_claims_count += 1
            else:
                # Semantic Sentence-BERT cosine similarity against evidence snippets
                sim_score, best_evidence = skill_embedding_model_instance.verify_claim_against_evidence(
                    claim_text, pool_snippets
                )
                
                if sim_score >= 80.0:
                    status = "Verified"
                    badge = "verified"
                    proj_verified += 1
                    verified_claims_count += 1
                elif sim_score >= 60.0:
                    status = "Partially Supported"
                    badge = "partial"
                    proj_partial += 1
                    partial_claims_count += 1
                else:
                    status = "Not Supported"
                    badge = "unsupported"
                    proj_unsupported += 1
                    unsupported_claims_count += 1
                    best_evidence = "No corresponding technical evidence found in retrieved public documentation"

            verified_items.append({
                "claim": claim_text,
                "claim_type": claim_type,
                "similarity_score": sim_score,
                "status": status,
                "badge": badge,
                "evidence_snippet": best_evidence
            })

        # Calculate project-level verification rate
        total_proj_items = len(claims)
        if total_proj_items > 0:
            proj_score = float(round(((proj_verified * 1.0 + proj_partial * 0.5) / total_proj_items) * 100, 2))
        else:
            proj_score = 75.0 if github_evidence_list else 0.0

        if proj_score >= 80.0:
            proj_verdict = "Strongly Supported"
        elif proj_score >= 55.0:
            proj_verdict = "Partially Supported"
        else:
            proj_verdict = "Limited Public Evidence"

        # Inconsistency detection (e.g. high discrepancy)
        if total_proj_items >= 3 and proj_score < 40.0 and specific_repo_evidence:
            inconsistencies.append({
                "project_title": proj_title,
                "repo_name": specific_repo_evidence.get("full_name"),
                "resume_claims": [c.get("claim") for c in claims[:4]],
                "repo_technologies": specific_repo_evidence.get("technologies", [])[:5],
                "message": f"Resume claims technologies ({', '.join([c.get('claim') for c in claims[:3]])}) for '{proj_title}', but public repository '{specific_repo_evidence.get('full_name')}' mainly contains evidence for {', '.join(specific_repo_evidence.get('technologies', [])[:3])}."
            })

        project_reports.append({
            "project_title": proj_title,
            "matched_repo": repo_matched,
            "verification_score": proj_score,
            "verdict": proj_verdict,
            "claims_breakdown": verified_items,
            "verified_count": proj_verified,
            "partial_count": proj_partial,
            "unsupported_count": proj_unsupported
        })

    # Overall Evidence Summary
    total_analyzed = max(1, total_claims_count)
    overall_evidence_rate = float(round(((verified_claims_count * 1.0 + partial_claims_count * 0.5) / total_analyzed) * 100, 2))
    
    if not github_evidence_list and not portfolio_evidence_list:
        overall_evidence_rate = 0.0

    return {
        "overall_evidence_score": overall_evidence_rate,
        "total_claims_analyzed": total_claims_count,
        "verified_claims_count": verified_claims_count,
        "partial_claims_count": partial_claims_count,
        "unsupported_claims_count": unsupported_claims_count,
        "project_reports": project_reports,
        "github_repositories_analyzed": github_evidence_list,
        "portfolios_analyzed": portfolio_evidence_list,
        "inconsistencies": inconsistencies
    }
