"""
URL Extractor & Normalizer for GitHub Repositories, LinkedIn Profiles, and Portfolio Links.
"""
import re
from typing import Dict, List, Optional, Tuple

GITHUB_REPO_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_\-\.]+)\/([a-zA-Z0-9_\-\.]+)',
    re.IGNORECASE
)

GITHUB_USER_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_\-\.]+)\/?$',
    re.IGNORECASE
)

LINKEDIN_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_\-\.]+)',
    re.IGNORECASE
)

def parse_github_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a GitHub URL into owner and repository name.
    """
    cleaned = url.strip().rstrip('/')
    repo_match = GITHUB_REPO_PATTERN.search(cleaned)
    if repo_match:
        owner = repo_match.group(1)
        repo = repo_match.group(2).replace('.git', '')
        return {
            "type": "repository",
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "url": f"https://github.com/{owner}/{repo}"
        }

    user_match = GITHUB_USER_PATTERN.search(cleaned)
    if user_match:
        user = user_match.group(1)
        return {
            "type": "user_profile",
            "owner": user,
            "repo": "",
            "full_name": user,
            "url": f"https://github.com/{user}"
        }

    return None

def parse_linkedin_url(url: str) -> Optional[Dict[str, str]]:
    """
    Parse a LinkedIn profile URL.
    """
    cleaned = url.strip().rstrip('/')
    match = LINKEDIN_PATTERN.search(cleaned)
    if match:
        username = match.group(1)
        return {
            "type": "linkedin_profile",
            "username": username,
            "url": f"https://linkedin.com/in/{username}"
        }
    return None

def extract_project_evidence_urls(resume_text: str, detected_urls: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """
    Filter and categorize public evidence links into GitHub repositories, GitHub profiles, LinkedIn profiles, and Portfolios.
    """
    github_repos = []
    github_profiles = []
    linkedin_profiles = []
    portfolios = []

    seen = set()

    for url in detected_urls:
        if not url or url in seen:
            continue
        seen.add(url)

        parsed_gh = parse_github_url(url)
        parsed_li = parse_linkedin_url(url)

        if parsed_gh:
            if parsed_gh["type"] == "repository":
                github_repos.append(parsed_gh)
            else:
                github_profiles.append(parsed_gh)
        elif parsed_li:
            linkedin_profiles.append(parsed_li)
        elif not any(d in url.lower() for d in ["twitter.com", "facebook.com", "instagram.com", "t.co"]):
            portfolios.append({
                "type": "portfolio",
                "url": url if url.startswith("http") else f"https://{url}"
            })

    return {
        "github_repositories": github_repos,
        "github_profiles": github_profiles,
        "linkedin_profiles": linkedin_profiles,
        "portfolio_websites": portfolios
    }
