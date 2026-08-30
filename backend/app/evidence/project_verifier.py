"""
Multi-Source Public Evidence Verifier Engine.
Performs semantic claim-by-claim verification between Resume Claims and Public Evidence sources:
  1. GitHub Multi-Repository Analysis (Code, READMEs, dependencies, languages)
  2. LinkedIn Profile & Career Intelligence (Headline, About, Experience, Certifications, Post Topics)
  3. Public Portfolio Websites
Assigns 3-state categorization (🟢 Verified, 🟡 Partially Supported, 🔴 Not Supported) with rich source citations.
"""
from typing import List, Dict, Any, Set, Tuple, Optional
from app.models.skill_embedding_model import skill_embedding_model_instance
from app.utils.skills import normalize_skill

def verify_project_claims(
    resume_project_claims: List[Dict[str, Any]],
    github_evidence_list: List[Dict[str, Any]],
    portfolio_evidence_list: List[Dict[str, Any]],
    linkedin_evidence: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Verify all resume claims against multi-source public evidence.
    """
    # 1. Consolidate evidence snippets with clear source attribution
    all_evidence_snippets: List[Tuple[str, str]] = [] # (snippet_text, source_tag)
    all_evidence_technologies: Set[str] = set()

    # GitHub Evidence
    for gh in github_evidence_list:
        repo_name = gh.get("repo_name") or gh.get("full_name") or "GitHub"
        for s in gh.get("evidence_snippets", []):
            all_evidence_snippets.append((s, f"[GitHub: {repo_name}]"))
        if gh.get("description"):
            all_evidence_snippets.append((gh.get("description"), f"[GitHub: {repo_name}]"))
        if gh.get("readme_preview"):
            all_evidence_snippets.append((gh.get("readme_preview"), f"[GitHub README: {repo_name}]"))
        for t in gh.get("technologies", []):
            all_evidence_technologies.add(normalize_skill(t))
        for l in gh.get("languages", []):
            all_evidence_technologies.add(normalize_skill(l))

    # LinkedIn Career & Activity Evidence
    if linkedin_evidence and linkedin_evidence.get("is_accessible"):
        li_user = linkedin_evidence.get("username") or "LinkedIn"
        for s in linkedin_evidence.get("evidence_snippets", []):
            all_evidence_snippets.append((s, f"[LinkedIn: {li_user}]"))
        for t in linkedin_evidence.get("skills", []):
            all_evidence_technologies.add(normalize_skill(t))

    # Portfolio Evidence
    for pf in portfolio_evidence_list:
        pf_url = pf.get("title") or pf.get("url") or "Portfolio"
        for s in pf.get("evidence_snippets", []):
            all_evidence_snippets.append((s, f"[Portfolio: {pf_url}]"))
        for t in pf.get("technologies", []):
            all_evidence_technologies.add(normalize_skill(t))

    # 2. Claim-by-Claim Verification
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

        # Find repository closely matching project name
        specific_repo = None
        for gh in github_evidence_list:
            r_name = gh.get("repo_name", "").lower()
            f_name = gh.get("full_name", "").lower()
            if (r_name in proj_title.lower() or 
                proj_title.lower() in r_name or
                proj_title.lower().replace(" ", "-") in f_name):
                specific_repo = gh
                break

        # Pool selection (prefer project-specific snippets first, fall back to global)
        if specific_repo:
            repo_n = specific_repo.get("repo_name")
            pool_snippets = [(s, f"[GitHub: {repo_n}]") for s in specific_repo.get("evidence_snippets", [])]
            if specific_repo.get("description"):
                pool_snippets.append((specific_repo.get("description"), f"[GitHub: {repo_n}]"))
            if specific_repo.get("readme_preview"):
                pool_snippets.append((specific_repo.get("readme_preview"), f"[GitHub README: {repo_n}]"))
            # Append other global evidence (LinkedIn, etc.)
            pool_snippets.extend([item for item in all_evidence_snippets if "[GitHub:" not in item[1]])
            pool_tech = {normalize_skill(t) for t in specific_repo.get("technologies", [])}
            matched_repo_name = specific_repo.get("full_name")
        else:
            pool_snippets = all_evidence_snippets
            pool_tech = all_evidence_technologies
            matched_repo_name = None

        raw_snippet_texts = [item[0] for item in pool_snippets if item[0] and len(item[0].strip()) > 3]

        proj_verified = 0
        proj_partial = 0
        proj_unsupported = 0

        for item in claims:
            total_claims_count += 1
            claim_text = item.get("claim", "")
            claim_type = item.get("claim_type", "Technology / Skill")
            norm_claim = normalize_skill(claim_text)

            # Always initialize matching_source before if/else
            matching_source = f"[GitHub: {matched_repo_name}]" if matched_repo_name else "[Public Evidence]"

            # Direct exact token match
            if norm_claim in pool_tech:
                sim_score = 100.0
                status = "Verified"
                badge = "verified"
                best_evidence = f"{matching_source} Found in technical metadata ({claim_text})"
                proj_verified += 1
                verified_claims_count += 1
            else:
                # Semantic Sentence-BERT embedding similarity match
                sim_score, matched_snippet = skill_embedding_model_instance.verify_claim_against_evidence(
                    claim_text, raw_snippet_texts
                )

                # Find source tag for the matching snippet
                for snip_text, src_tag in pool_snippets:
                    if snip_text == matched_snippet:
                        matching_source = src_tag
                        break

                if sim_score >= 80.0:
                    status = "Verified"
                    badge = "verified"
                    best_evidence = f"{matching_source} {matched_snippet}"
                    proj_verified += 1
                    verified_claims_count += 1
                elif sim_score >= 60.0:
                    status = "Partially Supported"
                    badge = "partial"
                    best_evidence = f"{matching_source} Related finding: {matched_snippet}"
                    proj_partial += 1
                    partial_claims_count += 1
                else:
                    status = "Not Supported"
                    badge = "unsupported"
                    best_evidence = "No corresponding technical evidence found in retrieved public repositories"
                    proj_unsupported += 1
                    unsupported_claims_count += 1

            source_url = None
            if matching_source and "[GitHub:" in matching_source:
                repo_part = matching_source.split("[GitHub:")[1].split("]")[0].strip()
                # repo_part may be "owner/repo" (full_name) or just "repo"
                source_url = f"https://github.com/{repo_part}"
            elif matching_source and "[GitHub README:" in matching_source:
                repo_part = matching_source.split("[GitHub README:")[1].split("]")[0].strip()
                source_url = f"https://github.com/{repo_part}"
            elif matching_source and "[LinkedIn:" in matching_source:
                li_part = matching_source.split("[LinkedIn:")[1].split("]")[0].strip()
                source_url = f"https://linkedin.com/in/{li_part}"
            elif matched_repo_name:
                source_url = f"https://github.com/{matched_repo_name}"

            verified_items.append({
                "claim": claim_text,
                "claim_type": claim_type,
                "similarity_score": sim_score,
                "status": status,
                "badge": badge,
                "evidence_snippet": best_evidence,
                "source_url": source_url
            })

        total_proj_items = max(1, len(claims))
        proj_score = float(round(((proj_verified * 1.0 + proj_partial * 0.5) / total_proj_items) * 100, 2))

        if proj_score >= 80.0:
            proj_verdict = "Strongly Supported"
        elif proj_score >= 55.0:
            proj_verdict = "Partially Supported"
        else:
            proj_verdict = "Limited Public Evidence"

        # Check for discrepancy
        if len(claims) >= 3 and proj_score < 40.0 and specific_repo:
            inconsistencies.append({
                "project_title": proj_title,
                "repo_name": specific_repo.get("full_name"),
                "resume_claims": [c.get("claim") for c in claims[:4]],
                "repo_technologies": specific_repo.get("technologies", [])[:5],
                "message": f"Resume claims technologies ({', '.join([c.get('claim') for c in claims[:3]])}) for '{proj_title}', but public repository '{specific_repo.get('full_name')}' mainly contains code for {', '.join(specific_repo.get('technologies', [])[:3])}."
            })

        project_reports.append({
            "project_title": proj_title,
            "matched_repo": matched_repo_name,
            "verification_score": proj_score,
            "verdict": proj_verdict,
            "claims_breakdown": verified_items,
            "verified_count": proj_verified,
            "partial_count": proj_partial,
            "unsupported_count": proj_unsupported
        })

    # Overall summary calculation
    total_analyzed = max(1, total_claims_count)
    overall_rate = float(round(((verified_claims_count * 1.0 + partial_claims_count * 0.5) / total_analyzed) * 100, 2))

    if not github_evidence_list and not portfolio_evidence_list and not (linkedin_evidence and linkedin_evidence.get("is_accessible")):
        overall_rate = 0.0

    return {
        "overall_evidence_score": overall_rate,
        "total_claims_analyzed": total_claims_count,
        "verified_claims_count": verified_claims_count,
        "partial_claims_count": partial_claims_count,
        "unsupported_claims_count": unsupported_claims_count,
        "project_reports": project_reports,
        "github_repositories_analyzed": github_evidence_list,
        "linkedin_evidence": linkedin_evidence,
        "portfolios_analyzed": portfolio_evidence_list,
        "inconsistencies": inconsistencies
    }
