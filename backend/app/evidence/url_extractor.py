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
            "github_username": owner,
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
            "github_username": user,
            "full_name": user,
            "url": f"https://github.com/{user}"
        }

    return None

def extract_github_username(url: str) -> Optional[str]:
    """
    Extract and normalize GitHub username from any valid GitHub URL format.
    Examples:
        github.com/username -> username
        https://github.com/username/ -> username
        https://www.github.com/username -> username
        https://github.com/username/repo -> username
    """
    if not url or not isinstance(url, str):
        return None
    cleaned = url.strip().strip('"').strip("'").rstrip('/')
    if not cleaned:
        return None
    if not cleaned.startswith("http://") and not cleaned.startswith("https://"):
        cleaned = "https://" + cleaned

    parsed = parse_github_url(cleaned)
    if parsed and parsed.get("owner"):
        return parsed["owner"]

    m = re.search(r'(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9_\-\.]+)', url, re.IGNORECASE)
    if m:
        u = m.group(1).rstrip('/')
        if u.lower() not in ["features", "pricing", "enterprise", "login", "signup", "about", "contact", "explore"]:
            return u
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
    Also scans resume_text for URLs preceded by portfolio-like labels (e.g. "Portfolio: https://...")
    that the PDF parser may have missed.
    """
    github_repos = []
    github_profiles = []
    linkedin_profiles = []
    portfolios = []

    # Scan resume text for URLs labelled with portfolio-like keywords.
    # Catches patterns like:
    #   Portfolio: https://mysite.com
    #   Portfolio URL: mysite.com
    #   Portfolio Website URL: myapp.vercel.app
    #   Portfolio Website: mysite.netlify.app/projects
    #   Portfolio Site: johndoe.github.io
    #   Portfolio Link — https://mysite.com
    #   Personal Website — https://mysite.com/projects
    #   Portfolio | mysite.io
    #   Website: www.mysite.dev
    PORTFOLIO_LABEL_RE = re.compile(
        r'(?:portfolio(?:\s+(?:website|site|page|link))?\s*(?:url)?'  # "Portfolio", "Portfolio Website", "Portfolio Website URL", "Portfolio Site", etc.
        r'|personal\s*(?:website|site|page|portfolio)'               # "Personal Website", "Personal Site", etc.
        r'|website|web\s*portfolio)'                                 # "Website", "Web Portfolio"
        r'\s*[:\-—–|]?\s*'                                           # separator: colon, dash, pipe, or just whitespace
        r'((?:https?://)?'                                           # URL start (protocol optional)
        r'(?:www\.)?'
        r'[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?'               # subdomain or domain (e.g. "myapp")
        r'(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?)*'        # additional subdomains (e.g. ".vercel")
        r'\.[a-zA-Z]{2,}'                                            # final TLD (e.g. ".app", ".io", ".com")
        r'(?:/[^\s,;)\"\']*)?)',                                     # optional path
        re.IGNORECASE
    )
    for match in PORTFOLIO_LABEL_RE.finditer(resume_text):
        url = match.group(1).rstrip('.,;:)\"\' ')
        if url and url not in detected_urls:
            detected_urls.append(url)

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

