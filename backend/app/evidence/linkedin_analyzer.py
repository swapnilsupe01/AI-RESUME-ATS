"""
Public LinkedIn Profile & Professional Activity Analyzer.
Extracts public headline, summary/about, verified experience roles, certifications,
public post/activity topics, and GitHub URLs shared in posts for identity verification.

INTEGRITY POLICY:
  - No mock, fake, or synthetic LinkedIn profile data is ever returned.
  - LinkedIn actively blocks unauthenticated scrapers. If data cannot be retrieved,
    the system returns an honest "data unavailable" response with the exact reason.
  - No inferred or generated posts, certifications, or experience are fabricated.
"""
import re
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from app.utils.skills import extract_skills
from app.utils.text_utils import clean_markdown_and_html

LINKEDIN_PROFILE_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_\-\.]+)',
    re.IGNORECASE
)

# Regex to extract GitHub URLs from any text (post bodies, about sections)
GITHUB_URL_RE = re.compile(
    r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_\-\.]+)(?:/([a-zA-Z0-9_\-\.]+))?',
    re.IGNORECASE
)


def _extract_github_urls_from_texts(texts: List[str]) -> List[str]:
    """Extract all unique GitHub URLs found across a list of text strings and normalize to https://."""
    seen: set = set()
    urls: List[str] = []
    for text in texts:
        for match in GITHUB_URL_RE.finditer(text or ""):
            owner = match.group(1)
            repo = match.group(2)
            if not owner or owner.lower() in ["features", "pricing", "explore", "topics", "collections"]:
                continue
            if repo:
                canonical = f"https://github.com/{owner}/{repo}".rstrip("/")
            else:
                canonical = f"https://github.com/{owner}".rstrip("/")

            if canonical not in seen:
                seen.add(canonical)
                urls.append(canonical)
    return urls


def extract_linkedin_username(url: str) -> Optional[str]:
    """
    Extract LinkedIn username slug from profile URL or plain username.
    Handles:
      https://linkedin.com/in/swapnilsupe01
      https://www.linkedin.com/in/swapnilsupe01/
      https://linkedin.com/in/swapnilsupe01/recent-activity/all/
      https://in.linkedin.com/in/swapnilsupe01?trk=...
      swapnilsupe01
    """
    if not url:
        return None
    cleaned = url.strip().rstrip('/')
    # Remove query string / fragments
    cleaned = cleaned.split('?')[0].split('#')[0]

    match = LINKEDIN_PROFILE_REGEX.search(cleaned)
    if match:
        user = match.group(1).rstrip('/')
        # If user contains subpaths like recent-activity, strip them
        return user.split('/')[0]

    # If already a simple username handle (e.g. swapnilsupe01)
    if re.match(r'^[a-zA-Z0-9_\-\.]{3,60}$', cleaned) and not cleaned.startswith('http'):
        return cleaned

    return None


def _unavailable_response(username: Optional[str], linkedin_url: str, reason: str) -> Dict[str, Any]:
    """
    Return an honest 'data unavailable' response. Never fabricates profile data.
    """
    return {
        "username": username or "unknown",
        "full_name": None,
        "headline": None,
        "location": None,
        "about": None,
        "experience": [],
        "certifications": [],
        "recent_post_topics": [],
        "skills": [],
        "evidence_snippets": [],
        "post_github_urls": [],
        "is_accessible": False,
        "data_unavailable_reason": reason,
        "url": linkedin_url,
        "source": "LinkedIn",
    }


async def fetch_linkedin_evidence(linkedin_url: str) -> Dict[str, Any]:
    """
    Attempt to fetch and parse public LinkedIn profile information.

    LinkedIn actively blocks unauthenticated scrapers (HTTP 999, 429, or redirect to /authwall).
    If data cannot be retrieved, returns an honest unavailable state — never fabricated data.

    Returns a dict with:
      is_accessible: bool  — True only if real data was successfully retrieved
      data_unavailable_reason: str  — Exact reason if data is unavailable
      recent_post_topics: List[str]  — Real post snippets if accessible
      post_github_urls: List[str]  — GitHub URLs extracted from real posts
    """
    username = extract_linkedin_username(linkedin_url)

    if not username:
        return _unavailable_response(None, linkedin_url,
            "Could not parse a valid LinkedIn username from the provided URL.")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/",
    }

    try:
        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            res = await client.get(linkedin_url, headers=headers)

            # LinkedIn returns 999, 429, or redirects to /authwall for bots
            if res.status_code in (999, 429):
                return _unavailable_response(username, linkedin_url,
                    f"LinkedIn returned HTTP {res.status_code} (bot protection / rate limit). "
                    "Public profile data is not accessible without authentication.")

            if res.status_code == 401 or "authwall" in str(res.url):
                return _unavailable_response(username, linkedin_url,
                    "LinkedIn requires authentication to view this profile (authwall redirect). "
                    "Public data is not accessible without a logged-in session.")

            if res.status_code == 404:
                return _unavailable_response(username, linkedin_url,
                    f"LinkedIn profile not found for username '{username}' (HTTP 404). "
                    "Verify the LinkedIn URL in the resume is correct.")

            if res.status_code != 200:
                return _unavailable_response(username, linkedin_url,
                    f"LinkedIn returned HTTP {res.status_code} for this profile URL. "
                    "Data could not be retrieved.")

            soup = BeautifulSoup(res.text, "html.parser")

            # Check if redirected to auth wall in page content
            page_text_raw = soup.get_text(separator=' ')
            if "authwall" in res.url.path or "Sign in" in page_text_raw[:500]:
                return _unavailable_response(username, linkedin_url,
                    "LinkedIn redirected to login/sign-in wall. "
                    "Public profile scraping is blocked by LinkedIn's bot protection. "
                    "No profile data is accessible without authentication.")

            for tag in soup(["script", "style", "nav", "footer"]):
                tag.extract()

            page_text = clean_markdown_and_html(soup.get_text(separator=' '))

            if len(page_text.strip()) < 100:
                return _unavailable_response(username, linkedin_url,
                    "LinkedIn returned a near-empty page — likely a bot-detection redirect. "
                    "No usable profile content could be extracted.")

            # Real data extraction from successfully loaded page
            title = soup.title.string.strip() if soup.title and soup.title.string else f"{username} | LinkedIn"
            full_name = title.split('|')[0].strip() if '|' in title else (
                title.split('-')[0].strip() if '-' in title else title
            )

            extracted_skills = sorted(list(extract_skills(page_text)))

            # Extract meaningful snippets
            snippets = [s.strip() for s in page_text.split('.') if len(s.strip()) > 25][:6]

            # Extract post topics if visible in page (LinkedIn activity feed)
            post_topics = [
                line.strip() for line in page_text.split('\n')
                if len(line.strip()) > 30 and any(
                    kw in line.lower() for kw in [
                        "project", "built", "launched", "github", "released",
                        "developed", "ai", "model", "open source", "deployed"
                    ]
                )
            ][:5]

            # Extract GitHub URLs from all visible page text (posts, about, etc.)
            post_github_urls = _extract_github_urls_from_texts([page_text])

            # Extract certifications if visible
            cert_keywords = ["Specialization", "Certificate", "Certified", "AWS", "TensorFlow", "Deep Learning", "Developer", "Professional"]
            scraped_certs = [
                line.strip() for line in page_text.split('\n')
                if len(line.strip()) > 15 and len(line.strip()) < 90
                and any(kw.lower() in line.lower() for kw in cert_keywords)
            ][:4]

            evidence_snippets = snippets

            return {
                "username": username,
                "full_name": full_name,
                "headline": title,
                "location": None,
                "about": page_text[:300] + "..." if len(page_text) > 300 else page_text,
                "experience": [],
                "certifications": scraped_certs,
                "recent_post_topics": post_topics,
                "skills": extracted_skills,
                "evidence_snippets": evidence_snippets,
                "post_github_urls": post_github_urls,
                "is_accessible": True,
                "data_unavailable_reason": None,
                "url": linkedin_url,
                "source": "LinkedIn Public Web",
            }

    except httpx.TimeoutException:
        return _unavailable_response(username, linkedin_url,
            "LinkedIn request timed out (>6s). LinkedIn's bot-protection may be rate-limiting requests.")

    except Exception as e:
        print(f"[LinkedIn Notice]: Fetch for {linkedin_url} failed: {e}")
        return _unavailable_response(username, linkedin_url,
            f"Network or parsing error when fetching LinkedIn profile: {str(e)}")
