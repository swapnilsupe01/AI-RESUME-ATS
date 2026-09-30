"""
GitHub Repository Activity & Evidence Service.
Formats repository-grouped contribution evidence, emphasizes development rigor
and activity evidence over raw commit counts, and handles public/private visibility.
Also fetches README.md and repository metadata for Layer F Codebase RAG grounding.
"""
from typing import List, Dict, Any, Optional
import httpx
import logging
from app.github.github_models import RepositoryContribution
from app.github.oauth_service import get_current_token

logger = logging.getLogger(__name__)

def format_repository_evidence(
    repos: List[RepositoryContribution],
    has_restricted: bool = False
) -> Dict[str, Any]:
    """
    Format repository evidence ensuring transparency and avoiding superficial quality assumptions.
    Rule 9: Never confuse commit count with contribution quality.
    Rule 16: Clearly distinguish public vs private/restricted contributions.
    """
    total_commits = sum(r.commit_count for r in repos)
    public_repos = [r for r in repos if not r.is_private]
    private_repos = [r for r in repos if r.is_private]

    evidence_summary = []
    for r in repos[:10]:
        evidence_summary.append({
            "repo_name": r.repository_name,
            "url": r.url,
            "commits": r.commit_count,
            "is_private": r.is_private,
            "language": r.primary_language or "General",
            "evidence_type": "Public Repository Activity" if not r.is_private else "Restricted / Private Repository Activity",
            "note": "Candidate recorded direct commit participation"
        })

    visibility_notes = []
    if has_restricted:
        visibility_notes.append("Candidate has anonymized/restricted private contribution activity enabled on GitHub.")
    if private_repos:
        visibility_notes.append(f"{len(private_repos)} private repositories included in contribution count.")
    else:
        visibility_notes.append("Private contribution details are not available via public scope.")

    return {
        "total_repositories": len(repos),
        "total_commits": total_commits,
        "repositories": [r.dict() for r in repos],
        "top_evidence": evidence_summary,
        "visibility_notes": visibility_notes,
        "evaluation_guidance": (
            "Recruiter Notice: Commit count alone does not establish engineering quality. "
            "Examine repository structure, test coverage, code architecture, and pull request activity "
            "for verified technical competency."
        )
    }


async def fetch_repository_readme(
    full_name_or_url: str,
    token: Optional[str] = None,
) -> Optional[str]:
    """
    Fetch raw README.md content from GitHub repository.
    Accepts full_name (e.g. 'octocat/Hello-World') or GitHub repo URL.
    """
    if not full_name_or_url:
        return None

    repo_path = full_name_or_url.strip()
    if "github.com/" in repo_path:
        parts = repo_path.split("github.com/")[-1].strip("/").split("/")
        if len(parts) >= 2:
            repo_path = f"{parts[0]}/{parts[1]}"
        else:
            return None

    auth_token = token or get_current_token()
    headers = {
        "Accept": "application/vnd.github.raw",
        "User-Agent": "AI-Resume-ATS/2.0",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    url = f"https://api.github.com/repos/{repo_path}/readme"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.text
            elif resp.status_code == 404:
                logger.debug("No README found for %s", repo_path)
            else:
                logger.debug("README fetch error %s: status %d", repo_path, resp.status_code)
    except Exception as exc:
        logger.debug("README fetch exception for %s: %s", repo_path, exc)

    return None


async def fetch_user_repositories_evidence(
    username: str,
    token: Optional[str] = None,
    max_repos: int = 10,
) -> List[Dict[str, Any]]:
    """
    Fetches top repositories and their README files for a GitHub user.
    Packages the data as verified code evidence for Layer F RAG indexing.
    """
    clean_user = username.strip().lstrip("@")
    if not clean_user:
        return []

    auth_token = token or get_current_token()
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Resume-ATS/2.0",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    repos_data = []
    try:
        url = f"https://api.github.com/users/{clean_user}/repos?sort=pushed&direction=desc&per_page={max_repos}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                repos_data = resp.json()
    except Exception as exc:
        logger.debug("Error fetching repos for %s: %s", clean_user, exc)
        return []

    if not isinstance(repos_data, list):
        return []

    evidence_list: List[Dict[str, Any]] = []

    for r in repos_data[:max_repos]:
        if not isinstance(r, dict):
            continue
        repo_name = r.get("name") or "repo"
        full_name = r.get("full_name") or f"{clean_user}/{repo_name}"
        desc = r.get("description") or ""
        lang = r.get("language")
        topics = r.get("topics") or []
        html_url = r.get("html_url") or f"https://github.com/{full_name}"

        techs = []
        if lang:
            techs.append(lang)
        techs.extend([t for t in topics if t])

        # Fetch README
        readme_content = await fetch_repository_readme(full_name, token=auth_token)

        evidence_snippets = []
        if desc:
            evidence_snippets.append(f"Repository Purpose: {desc}")
        if topics:
            evidence_snippets.append(f"Topics / Tags: {', '.join(topics)}")

        evidence_list.append({
            "repo_name": repo_name,
            "full_name": full_name,
            "url": html_url,
            "description": desc,
            "languages": [lang] if lang else [],
            "technologies": techs,
            "evidence_snippets": evidence_snippets,
            "readme_content": readme_content or "",
        })

    return evidence_list

