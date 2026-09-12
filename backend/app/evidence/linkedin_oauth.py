"""
LinkedIn OAuth 2.0 & OpenID Connect Service.
Provides ethical, official identity verification using LinkedIn OpenID Connect:
  - Scopes: openid, profile, email
  - Validates applicant identity against resume claims (Name, Email)
  - Complies strictly with LinkedIn terms: zero scraping, no cookie extraction, no authwall bypass.

FIXES vs. previous version:
  1. Sessions are now keyed per candidate/session ID instead of one shared global
     dict. The previous CURRENT_LINKEDIN_SESSION global meant concurrent candidates
     could overwrite each other's verified identity — candidate A's audit could end
     up reading candidate B's LinkedIn result. This is fixed by storing verified
     sessions in a dict keyed by session_id (recommend using the same candidate/audit
     ID already used elsewhere in the pipeline).
  2. When there's no comparable data (LinkedIn didn't return a name/email, or the
     resume itself lacks one), the result no longer defaults to match_score=85.0 /
     status="VERIFIED". That was asserting a match happened when no comparison was
     actually possible. It now returns a distinct "AUTHENTICATED_NO_COMPARISON_DATA"
     status with match_score=None, so callers can tell "verified and matches" apart
     from "authenticated, but we couldn't check."
  3. generate_linkedin_oauth_url now URL-encodes the query string via urlencode
     instead of manual string interpolation (scope contains spaces; redirect_uri
     contains reserved characters like ':' and '/').

BACKWARD COMPATIBILITY: if any existing caller reads CURRENT_LINKEDIN_SESSION
directly as a module-level variable, that access pattern needs to change to
get_linkedin_session(session_id) — see the note above the store below. A
best-effort DEFAULT_SESSION_KEY fallback is kept so single-user/local usage
keeps working without changes, but multi-user deployments MUST pass a real
session_id through the OAuth flow (state -> session_id mapping, e.g. via the
candidate's audit ID) for the fix in #1 to actually take effect.
"""
import os
import secrets
from urllib.parse import urlencode
import httpx
from typing import Optional, Dict, List, Tuple, Any
from datetime import datetime, timezone

LINKEDIN_CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID", "")
LINKEDIN_CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET", "")
LINKEDIN_REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/api/linkedin/callback")

# In-memory storage for active LinkedIn OAuth states.
# state -> {"resume_name": str, "resume_email": str, "session_id": str, "created_at": float}
LINKEDIN_OAUTH_STATES: Dict[str, Dict[str, Any]] = {}

# Verified LinkedIn sessions, keyed by session_id (NOT a single shared global).
# Pass a real per-candidate session_id (e.g. the audit/report ID) through
# generate_linkedin_oauth_url -> validate_linkedin_oauth_state -> verify_linkedin_identity
# so concurrent candidates never share or overwrite each other's result.
LINKEDIN_SESSIONS: Dict[str, Dict[str, Any]] = {}
DEFAULT_SESSION_KEY = "_default_single_user_session"  # fallback only for local/single-user use

# Backward-compatible alias — linkedin_routes.py and any other caller that imported
# CURRENT_LINKEDIN_SESSION directly will still resolve. For multi-user deployments
# use get_linkedin_session(session_id) instead of reading this directly.
CURRENT_LINKEDIN_SESSION: Dict[str, Any] = LINKEDIN_SESSIONS.setdefault(DEFAULT_SESSION_KEY, {
    "is_verified": False,
    "status": "NOT_PROVIDED",
    "sub": None,
    "name": None,
    "email": None,
    "picture": None,
    "verified_at": None,
    "match_score": None,
    "details": [],
})


def is_linkedin_configured() -> bool:
    """Check if LinkedIn OAuth credentials are configured."""
    return bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)


def generate_linkedin_oauth_url(
    resume_name: Optional[str] = None,
    resume_email: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Generate LinkedIn OAuth 2.0 authorization URL using OpenID Connect.

    `session_id` should be the candidate/audit identifier already used elsewhere
    in the pipeline. It's threaded through the OAuth state so that when the
    callback fires, the verified result can be stored against the right
    candidate instead of a single shared global.
    """
    state = secrets.token_urlsafe(24)
    LINKEDIN_OAUTH_STATES[state] = {
        "resume_name": resume_name.strip() if resume_name else None,
        "resume_email": resume_email.strip() if resume_email else None,
        "session_id": session_id or DEFAULT_SESSION_KEY,
    }

    params = {
        "response_type": "code",
        "client_id": LINKEDIN_CLIENT_ID,
        "redirect_uri": LINKEDIN_REDIRECT_URI,
        "state": state,
        "scope": "openid profile email",
    }
    auth_url = f"https://www.linkedin.com/oauth/v2/authorization?{urlencode(params)}"
    return auth_url, state


def validate_linkedin_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Validate and consume OAuth state token. Returns the stored context
    (resume_name, resume_email, session_id) or None if the state is invalid/expired/reused."""
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
        "client_secret": LINKEDIN_CLIENT_SECRET,
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
    resume_email: Optional[str],
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compare official authenticated LinkedIn identity against resume claims.
    Stores the result against `session_id` (defaulting to a single-user fallback
    key if none is provided) instead of a shared global, so concurrent candidates
    don't overwrite each other's verified identity.
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

    if total_checks == 0:
        # Candidate genuinely authenticated via LinkedIn, but there's nothing to
        # compare it against (missing name/email on one side or the other).
        # Do NOT claim this is "VERIFIED" — we have proof of a real LinkedIn
        # account, not proof it's the resume's claimed identity.
        match_score: Optional[float] = None
        status = "AUTHENTICATED_NO_COMPARISON_DATA"
        details.append(
            "Candidate authenticated via LinkedIn OAuth, but no comparable name/email "
            "data was available on both sides to confirm identity match."
        )
    else:
        match_score = round((matches / total_checks) * 100.0, 1)
        status = "VERIFIED" if match_score >= 50.0 else "INCONSISTENCY"

    result = {
        "is_verified": True,  # OAuth itself succeeded — see `status` for match confidence
        "status": status,
        "sub": auth_sub,
        "name": auth_name,
        "email": auth_email,
        "picture": auth_picture,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "match_score": match_score,
        "name_matched": name_matched,
        "email_matched": email_matched,
        "details": details,
    }

    key = session_id or DEFAULT_SESSION_KEY
    LINKEDIN_SESSIONS[key] = result
    return result


def get_linkedin_session(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve a candidate's verified LinkedIn session by session_id.
    Replaces direct access to the old CURRENT_LINKEDIN_SESSION global — update
    any call site that used to read that variable directly to call this instead.
    Returns an honest "not verified" shape if nothing is stored for this key.
    """
    key = session_id or DEFAULT_SESSION_KEY
    return LINKEDIN_SESSIONS.get(key, {
        "is_verified": False,
        "status": "NOT_PROVIDED",
        "sub": None,
        "name": None,
        "email": None,
        "picture": None,
        "verified_at": None,
        "match_score": None,
        "details": [],
    })