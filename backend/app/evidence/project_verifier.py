"""
Multi-Source Public Evidence Verifier Engine.
Performs semantic claim-by-claim verification between Resume Claims and Public Evidence sources:
  1. GitHub Multi-Repository Analysis (Code, READMEs, dependencies, languages)
  2. LinkedIn Profile & Career Intelligence (Headline, About, Experience, Certifications, Post Topics)
  3. Public Portfolio Websites
Assigns 4-state categorization (Verified, Partially Supported, Not Found, Unverifiable) with rich source citations.
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
    all_evidence_snippets: List[Tuple[str, str]] = []  # (snippet_text, source_tag)
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
    not_found_claims_count = 0
    unverifiable_claims_count = 0
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

        # Check if project has no repo and no github evidence available (or rate-limited/failed)
        has_repo_link = bool(proj.get("github_url") or proj.get("url") or specific_repo)
        api_rate_limited = any(gh.get("rate_limited") for gh in github_evidence_list) if github_evidence_list else False

        # Pool selection (prefer project-specific snippets first, fall back to global)
        if specific_repo:
            repo_n = specific_repo.get("repo_name")
            pool_snippets = [(s, f"[GitHub: {repo_n}]") for s in specific_repo.get("evidence_snippets", [])]
            if specific_repo.get("description"):
                pool_snippets.append((specific_repo.get("description"), f"[GitHub: {repo_n}]"))
            if specific_repo.get("readme_preview"):
                pool_snippets.append((specific_repo.get("readme_preview"), f"[GitHub README: {repo_n}]"))
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
        proj_not_found = 0
        proj_unverifiable = 0

        for item in claims:
            total_claims_count += 1
            claim_text = item.get("claim", "")
            claim_type = item.get("claim_type", "Technology / Skill")
            norm_claim = normalize_skill(claim_text)

            matching_source = f"[GitHub: {matched_repo_name}]" if matched_repo_name else "[Public Evidence]"
            evidence_file = "Metadata"

            if not specific_repo and not github_evidence_list and not has_repo_link:
                status = "Unverifiable"
                badge = "unverifiable"
                sim_score = 0.0
                evidence_file = "N/A"
                best_evidence = "Project has no public GitHub repository URL linked"
                proj_unverifiable += 1
                unverifiable_claims_count += 1
            elif api_rate_limited:
                status = "Unverifiable"
                badge = "unverifiable"
                sim_score = 0.0
                evidence_file = "API Rate Limit"
                best_evidence = "GitHub API rate limit exceeded during evidence scan"
                proj_unverifiable += 1
                unverifiable_claims_count += 1
            elif norm_claim in pool_tech:
                sim_score = 100.0
                status = "Verified"
                badge = "verified"
                evidence_file = specific_repo.get("repo_name", "package.json") if specific_repo else "dependencies"
                best_evidence = f"{matching_source} Found in technical metadata ({claim_text})"
                proj_verified += 1
                verified_claims_count += 1
            else:
                sim_score, matched_snippet = skill_embedding_model_instance.verify_claim_against_evidence(
                    claim_text, raw_snippet_texts
                )
                for snip_text, src_tag in pool_snippets:
                    if snip_text == matched_snippet:
                        matching_source = src_tag
                        break

                if "README" in matching_source:
                    evidence_file = "README.md"
                elif specific_repo:
                    evidence_file = specific_repo.get("repo_name") or "codebase"
                else:
                    evidence_file = "evidence"

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
                    if not specific_repo and not github_evidence_list:
                        status = "Unverifiable"
                        badge = "unverifiable"
                        evidence_file = "N/A"
                        best_evidence = "No public GitHub repository available to verify claim"
                        proj_unverifiable += 1
                        unverifiable_claims_count += 1
                    else:
                        status = "Not Found"
                        badge = "not_found"
                        best_evidence = "No corresponding technical evidence found in retrieved public repositories"
                        proj_not_found += 1
                        not_found_claims_count += 1

            source_url = None
            if matching_source and "[GitHub:" in matching_source:
                repo_part = matching_source.split("[GitHub:")[1].split("]")[0].strip()
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
                "evidence_file": evidence_file,
                "evidence_snippet": best_evidence,
                "source_url": source_url
            })

        # Exclude unverifiable claims from the denominator
        evaluable_proj_items = proj_verified + proj_partial + proj_not_found
        if evaluable_proj_items > 0:
            proj_score = float(round(((proj_verified * 1.0 + proj_partial * 0.5) / evaluable_proj_items) * 100, 2))
        else:
            proj_score = 100.0 if (github_evidence_list or specific_repo) else 0.0

        if proj_score >= 80.0:
            proj_verdict = "Strongly Supported"
        elif proj_score >= 55.0:
            proj_verdict = "Partially Supported"
        else:
            proj_verdict = "Limited Public Evidence"

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
            "unsupported_count": proj_not_found,
            "not_found_count": proj_not_found,
            "unverifiable_count": proj_unverifiable,
        })

    # Overall summary calculation — unverifiable claims excluded from denominator
    evaluable_overall = verified_claims_count + partial_claims_count + not_found_claims_count
    if evaluable_overall > 0:
        overall_rate = float(round(((verified_claims_count * 1.0 + partial_claims_count * 0.5) / evaluable_overall) * 100, 2))
    else:
        overall_rate = 0.0 if not github_evidence_list else 100.0

    return {
        "overall_evidence_score": overall_rate,
        "total_claims_analyzed": total_claims_count,
        "verified_claims_count": verified_claims_count,
        "partial_claims_count": partial_claims_count,
        "unsupported_claims_count": not_found_claims_count,
        "not_found_claims_count": not_found_claims_count,
        "unverifiable_claims_count": unverifiable_claims_count,
        "project_reports": project_reports,
        "github_repositories_analyzed": github_evidence_list,
        "linkedin_evidence": linkedin_evidence,
        "portfolios_analyzed": portfolio_evidence_list,
        "inconsistencies": inconsistencies
    }
