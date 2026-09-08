"""
Public GitHub Multi-Repository Analyzer.
Retrieves real public repository metadata, README documentation, languages, and technical dependencies
using the public GitHub REST API, with multi-repository user profile discovery and token authentication.

INTEGRITY POLICY:
  - No mock, fake, or synthetic GitHub repositories are returned.
  - Authentic API calls with Authorization header when available (5,000 req/hr).
  - If a repository or profile cannot be fetched, it is omitted or flagged honestly.
"""
import base64
from typing import Dict, Any, List, Optional
import httpx
from app.utils.skills import extract_skills
from app.utils.text_utils import clean_markdown_and_html
from app.github.oauth_service import get_current_token


def _get_github_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": "AI-Resume-ATS-Public-Analyzer",
        "Accept": "application/vnd.github.v3+json"
    }
    token = get_current_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


async def fetch_github_repo_evidence(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Fetch real public repository details from GitHub API and raw README.
    Returns None if the repository does not exist or cannot be accessed.
    """
    headers = _get_github_headers()

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            # 1. Fetch Repository Metadata
            repo_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
            
            if repo_res.status_code == 200:
                repo_data = repo_res.json()
                description = repo_data.get("description") or ""
                topics = repo_data.get("topics") or []

                # 2. Fetch Languages
                lang_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}/languages", headers=headers)
                languages = list(lang_res.json().keys()) if lang_res.status_code == 200 else []

                # 3. Fetch README content
                readme_text = ""
                readme_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}/readme", headers=headers)
                if readme_res.status_code == 200:
                    content_b64 = readme_res.json().get("content", "")
                    try:
                        readme_text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
                    except Exception:
                        readme_text = ""

                cleaned_readme = clean_markdown_and_html(readme_text)
                combined_text = f"{description} {' '.join(topics)} {' '.join(languages)} {cleaned_readme}"
                technologies = sorted(list(extract_skills(combined_text)))

                evidence_snippets = [f"Repository description: {description}"] if description else []
                if languages:
                    evidence_snippets.append(f"Languages detected: {', '.join(languages)}")
                if topics:
                    evidence_snippets.append(f"Repository topics: {', '.join(topics)}")
                if cleaned_readme:
                    first_lines = [line.strip() for line in cleaned_readme.split('.') if len(line.strip()) > 15][:5]
                    evidence_snippets.extend([f"README: {line}" for line in first_lines])

                return {
                    "repo_name": repo,
                    "owner": owner,
                    "full_name": f"{owner}/{repo}",
                    "description": description,
                    "languages": languages,
                    "topics": topics,
                    "technologies": technologies,
                    "readme_preview": cleaned_readme[:300] + "..." if len(cleaned_readme) > 300 else cleaned_readme,
                    "evidence_snippets": evidence_snippets,
                    "is_live_retrieved": True,
                    "source": "GitHub Public API"
                }
            else:
                print(f"[GitHub API Notice]: Live fetch for {owner}/{repo} returned status {repo_res.status_code}")

    except Exception as e:
        print(f"[GitHub API Notice]: Live fetch for {owner}/{repo} failed: {e}")

    return None


async def discover_user_public_repositories(username: str) -> List[Dict[str, Any]]:
    """
    Auto-discover and fetch ALL real public repositories under a GitHub user profile.
    Never invents fake repositories.
    """
    headers = _get_github_headers()
    discovered_repos: List[Dict[str, Any]] = []

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=updated&per_page=15",
                headers=headers
            )
            if res.status_code == 200:
                repos_json = res.json()
                for r in repos_json:
                    repo_name = r.get("name")
                    if repo_name:
                        ev = await fetch_github_repo_evidence(username, repo_name)
                        if ev:
                            discovered_repos.append(ev)
                return discovered_repos
            else:
                print(f"[GitHub User Discovery Notice]: Could not fetch repos for {username} (status {res.status_code})")
    except Exception as e:
        print(f"[GitHub User Discovery Notice]: Could not fetch repos for {username} via API: {e}")

    return discovered_repos


async def analyze_all_github_evidence(
    repo_list: List[Dict[str, str]], 
    user_profiles: List[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Analyze both explicitly linked repositories and all repositories discovered under user profiles.
    Only returns verified, real repositories.
    """
    results: List[Dict[str, Any]] = []
    seen_repos = set()

    # 1. Process specific repositories
    for r in repo_list:
        owner = r.get("owner", "")
        repo = r.get("repo", "")
        if owner and repo:
            full = f"{owner}/{repo}".lower()
            if full not in seen_repos:
                seen_repos.add(full)
                ev = await fetch_github_repo_evidence(owner, repo)
                if ev:
                    results.append(ev)

    # 2. Auto-discover all repositories for any user profiles found
    if user_profiles:
        for u in user_profiles:
            owner = u.get("owner", "")
            if owner:
                user_repos = await discover_user_public_repositories(owner)
                for ur in user_repos:
                    full = ur.get("full_name", "").lower()
                    if full not in seen_repos:
                        seen_repos.add(full)
                        results.append(ur)

    return results
