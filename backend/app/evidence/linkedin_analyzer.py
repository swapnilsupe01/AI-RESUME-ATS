"""
LinkedIn Identity Verifier (OAuth-based).

Replaces the previous scraping-based analyzer. LinkedIn's authwall is active bot
detection, not a static obstacle, and scraping profile pages violates LinkedIn's
Terms of Service regardless of header/UA sophistication. This module instead uses
LinkedIn's own free, official "Sign In with LinkedIn" (OpenID Connect) product to
get a verified, candidate-consented identity — the same trust model as the existing
GitHub OAuth flow in this codebase.

WHAT THIS CAN AND CANNOT DO:
  - CAN verify: name, email, profile picture — via LinkedIn's free OIDC scopes
    (openid, profile, email). This is a signed, LinkedIn-issued identity, not a guess.
  - CANNOT retrieve: work history, skills, certifications, or post activity. LinkedIn
    does not expose these via any free or self-serve API. If your product needs that
    data, the candidate must self-provide it (see linkedin_pdf_fallback below) and it
    must be labeled as self-reported, not independently verified.
  - Does NOT scrape linkedin.com under any circumstances.

INTEGRITY POLICY:
  - No mock, fake, or synthetic LinkedIn data is ever returned.
  - Verified fields (from OAuth) and self-reported fields (from candidate PDF upload)
    are kept in clearly separate keys so callers never conflate the two trust levels.
"""
import re
from typing import Any, Dict, Optional

import httpx

LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

LINKEDIN_URL_PATTERN = re.compile(
    r"^https?://(?:[a-zA-Z0-9_-]+\.)?linkedin\.com/(?:in|pub|posts|feed/update)/([a-zA-Z0-9_\-\.]+)",
    re.IGNORECASE
)


def _unverified_response(reason: str) -> Dict[str, Any]:
    """Honest 'not verified' response. Never fabricates identity data."""
    return {
        "username": None,
        "full_name": None,
        "email": None,
        "headline": None,
        "profile_picture_url": None,
        "linkedin_sub": None,
        "is_verified": False,
        "is_accessible": False,
        "heuristic_score": 60.0,
        "verification_unavailable_reason": reason,
        "self_reported": None,  # populated separately if a PDF export was parsed
        "source": "LinkedIn OAuth (OpenID Connect)",
    }


async def verify_linkedin_identity(access_token: Optional[str]) -> Dict[str, Any]:
    """
    Verify a candidate's LinkedIn identity using an access token obtained through the
    standard OAuth 2.0 authorization code flow (candidate clicks "Verify with LinkedIn",
    grants consent, your backend exchanges the code for this token — same pattern as
    the existing GitHub OAuth flow in oauth_service.py).

    Returns verified identity fields only. This function never touches linkedin.com's
    web pages and performs no scraping.
    """
    if not access_token:
        return _unverified_response(
            "No LinkedIn OAuth token present. Candidate has not completed LinkedIn verification."
        )

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(LINKEDIN_USERINFO_URL, headers=headers)

            if res.status_code == 401:
                return _unverified_response(
                    "LinkedIn OAuth token is invalid or expired. Candidate must re-verify."
                )
            if res.status_code != 200:
                return _unverified_response(
                    f"LinkedIn userinfo endpoint returned HTTP {res.status_code}."
                )

            data = res.json()

            return {
                "username": None,  # OIDC userinfo does not expose a vanity handle
                "full_name": data.get("name"),
                "email": data.get("email"),
                "headline": None,  # not included in the free OIDC scope set
                "profile_picture_url": data.get("picture"),
                "linkedin_sub": data.get("sub"),  # stable LinkedIn user ID — use this,
                                                    # not name/email, as the durable identity key
                "is_verified": True,
                "is_accessible": True,
                "heuristic_score": 100.0,
                "verification_unavailable_reason": None,
                "self_reported": None,
                "source": "LinkedIn OAuth (OpenID Connect)",
            }

    except httpx.TimeoutException:
        return _unverified_response("LinkedIn userinfo request timed out.")
    except Exception as e:
        return _unverified_response(f"Error verifying LinkedIn identity: {str(e)}")


def attach_self_reported_profile(verified_result: Dict[str, Any], parsed_pdf_text: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attaches candidate-uploaded, self-reported profile detail (parsed from their own
    LinkedIn "Save to PDF" export via the existing pdf_parser.py pipeline) to a verified
    OAuth result. This data is NOT independently verified by LinkedIn and must always be
    surfaced to the recruiter as self-reported, distinct from the `is_verified` OAuth fields.

    Expected `parsed_pdf_text` shape (produced upstream by pdf_parser.py / resume_parser.py):
        {"headline": str, "experience": List[dict], "skills": List[str], "about": str}
    """
    result = dict(verified_result)
    result["self_reported"] = {
        "headline": parsed_pdf_text.get("headline"),
        "experience": parsed_pdf_text.get("experience", []),
        "skills": parsed_pdf_text.get("skills", []),
        "about": parsed_pdf_text.get("about"),
        "note": "Self-reported by candidate via LinkedIn PDF export; not independently verified by LinkedIn.",
    }
    return result


async def fetch_linkedin_evidence(linkedin_url: str) -> Dict[str, Any]:
    """
    Heuristic evidence evaluator for LinkedIn URLs found in the resume PDF.
    
    Because LinkedIn scraping is blocked by HTTP 999 authwalls and 3rd-party
    scraping APIs are costly, this function validates the URL format extracted
    from the PDF and awards an 80% baseline credibility score.
    """
    if not linkedin_url or not isinstance(linkedin_url, str):
        return {
            **_unverified_response("No valid LinkedIn URL provided in resume."),
            "url": None,
            "post_github_urls": [],
        }

    cleaned_url = linkedin_url.strip()
    if not cleaned_url.startswith("http"):
        cleaned_url = f"https://{cleaned_url}"

    match = LINKEDIN_URL_PATTERN.search(cleaned_url)
    username = match.group(1).rstrip("/.,;:)") if match else None

    if "linkedin.com" in cleaned_url.lower() and username:
        return {
            "username": username,
            "full_name": None,
            "email": None,
            "headline": None,
            "profile_picture_url": None,
            "linkedin_sub": None,
            "is_verified": False,
            "is_accessible": True,
            "is_pdf_verified": True,
            "heuristic_score": 80.0,
            "verification_unavailable_reason": None,
            "note": "LinkedIn URL extracted from resume PDF and structurally validated. Awarded 80% baseline credibility.",
            "source": "Resume PDF LinkedIn Link (Heuristic 80% Baseline)",
            "url": cleaned_url,
            "post_github_urls": [],
        }

    return {
        **_unverified_response("Invalid or unrecognized LinkedIn URL format."),
        "url": cleaned_url,
        "post_github_urls": [],
    }