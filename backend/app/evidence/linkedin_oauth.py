"""
LinkedIn OAuth 2.0 & OpenID Connect Service.
Provides ethical, official identity verification using LinkedIn OpenID Connect:
  - Scopes: openid, profile, email
  - Validates applicant identity against resume claims (Name, Email)
  - Complies strictly with LinkedIn terms: zero scraping, no cookie extraction, no authwall bypass.
"""
import os
import secrets
import httpx
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timezone

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/linkedin/callback")

# In-memory storage for active LinkedIn OAuth states
# state -> {"resume_name": str, "resume_email": str, "created_at": float}
LINKEDIN_OAUTH_STATES: Dict[str, Dict[str, Any]] = {}

# Current verified LinkedIn session
CURRENT_LINKEDIN_SESSION: Dict[str, Any] = {
    "is_verified": False,
    "status": "NOT_PROVIDED",  # NOT_PROVIDED | URL_FOUND | PUBLIC_PROFILE_INACCESSIBLE | USER_AUTHENTICATED | VERIFIED | INCONSISTENCY
    "sub": None,
    "name": None,
    "email": None,
    "picture": None,
    "verified_at": None,
    "match_score": 0.0,
    "details": []
}


def is_linkedin_configured() -> bool:
    """Check if LinkedIn OAuth credentials are configured."""
    return bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)


def generate_linkedin_oauth_url(
    resume_name: Optional[str] = None,
    resume_email: Optional[str] = None
) -> Tuple[str, str]:
    """
    Generate LinkedIn OAuth 2.0 authorization URL using OpenID Connect.
    """
    state = secrets.token_urlsafe(24)
    LINKEDIN_OAUTH_STATES[state] = {
        "resume_name": resume_name.strip() if resume_name else None,
        "resume_email": resume_email.strip() if resume_email else None
    }

    client_id = LINKEDIN_CLIENT_ID
    redirect_uri = LINKEDIN_REDIRECT_URI
    scope = "openid profile email"

    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope={scope}"
    )
    return auth_url, state


def validate_linkedin_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Validate and consume OAuth state token."""
    return LINKEDIN_OAUTH_STATES.pop(state, None)


async def exchange_linkedin_code(code: str) -> Optional[str]:
    """Exchange authorization code for LinkedIn access token."""
    if not is_linkedin_configured():
        return None

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://www.linkedin.com/oauth/v2/accessToken", data=data, headers=headers)
            if resp.status_code == 200:
                token_data = resp.json()
                return token_data.get("access_token")
    except Exception as e:
        print(f"[LinkedIn OAuth Exchange Error]: {e}")

    return None


async def fetch_linkedin_userinfo(token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch authenticated user info from official OpenID Connect endpoint:
    GET https://api.linkedin.com/v2/userinfo
    """
    if not token:
        return None

    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get("https://api.linkedin.com/v2/userinfo", headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"[LinkedIn UserInfo Fetch Error]: {e}")

    return None


def verify_linkedin_identity(
    linkedin_user: Dict[str, Any],
    resume_name: Optional[str],
    resume_email: Optional[str]
) -> Dict[str, Any]:
    """
    Compare official authenticated LinkedIn identity against resume claims.
    """
    auth_name = linkedin_user.get("name", "").strip()
    auth_email = linkedin_user.get("email", "").strip().lower()
    auth_sub = linkedin_user.get("sub", "")
    auth_picture = linkedin_user.get("picture", "")

    details: List[str] = []
    matches = 0
    total_checks = 0

    # Name check
    name_matched = False
    if resume_name and auth_name:
        total_checks += 1
        r_parts = set(resume_name.lower().split())
        l_parts = set(auth_name.lower().split())
        common = r_parts.intersection(l_parts)
        if len(common) >= 1:
            name_matched = True
            matches += 1
            details.append(f"Name match verified: '{auth_name}' corresponds to resume '{resume_name}'.")
        else:
            details.append(f"Name divergence: LinkedIn name '{auth_name}' differs from resume name '{resume_name}'.")

    # Email check
    email_matched = False
    if resume_email and auth_email:
        total_checks += 1
        if resume_email.lower().strip() == auth_email:
            email_matched = True
            matches += 1
            details.append(f"Email address verified: '{auth_email}' matches resume contact email.")
        else:
            details.append(f"Email divergence: Authenticated LinkedIn email '{auth_email}' differs from resume email '{resume_email}'.")

    match_score = (matches / total_checks * 100.0) if total_checks > 0 else 85.0
    status = "VERIFIED" if match_score >= 50.0 else "INCONSISTENCY"

    result = {
        "is_verified": True,
        "status": status,
        "sub": auth_sub,
        "name": auth_name,
        "email": auth_email,
        "picture": auth_picture,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "match_score": round(match_score, 1),
        "name_matched": name_matched,
        "email_matched": email_matched,
        "details": details
    }

    global CURRENT_LINKEDIN_SESSION
    CURRENT_LINKEDIN_SESSION = result
    return result
