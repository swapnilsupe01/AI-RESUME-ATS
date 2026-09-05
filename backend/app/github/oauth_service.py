"""
GitHub OAuth & Token Authorization Service.
Handles GitHub OAuth URL generation, state validation, authorization code exchange,
and in-memory token cache for authenticated identity verification.
"""
import os
import secrets
import httpx
from typing import Optional, Dict, Tuple, Any

# Environment variables for GitHub OAuth
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:8000/api/github/callback")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# In-memory storage for active OAuth states and authenticated user tokens
# state -> {"resume_username": str, "created_at": float}
OAUTH_STATES: Dict[str, Dict[str, Any]] = {}

# Active authenticated session token cache
# login -> access_token
USER_TOKENS: Dict[str, str] = {}
# Global active authenticated session for single-user local ATS
CURRENT_SESSION: Dict[str, Any] = {
    "access_token": GITHUB_TOKEN if GITHUB_TOKEN else None,
    "login": None,
    "github_user_id": None,
    "avatar_url": None,
    "verified_at": None,
    "resume_username": None
}

def generate_oauth_url(resume_username: Optional[str] = None) -> Tuple[str, str]:
    """
    Generate the GitHub OAuth authorization URL with CSRF state token.
    Scope includes `read:user` and `repo` (to read public/private contributions).
    """
    state = secrets.token_urlsafe(24)
    OAUTH_STATES[state] = {
        "resume_username": resume_username.strip() if resume_username else None
    }

    client_id = GITHUB_CLIENT_ID
    redirect_uri = GITHUB_REDIRECT_URI
    scope = "read:user repo"

    auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&state={state}"
    )
    return auth_url, state

def validate_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """Validate and consume OAuth state token."""
    return OAUTH_STATES.pop(state, None)

async def exchange_code_for_token(code: str) -> Optional[str]:
    """
    Exchange authorization code for a GitHub access token.
    Uses POST https://github.com/login/oauth/access_token.
    """
    if not GITHUB_CLIENT_ID or not GITHUB_CLIENT_SECRET:
        return None

    url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": GITHUB_REDIRECT_URI
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("access_token")
    except Exception as e:
        print(f"[GitHub OAuth Error]: Failed to exchange code: {e}")

    return None

def set_current_session(token: str, login: str, github_user_id: int, avatar_url: Optional[str], resume_username: Optional[str], verified_at: str):
    """Set the currently active authenticated session."""
    CURRENT_SESSION["access_token"] = token
    CURRENT_SESSION["login"] = login
    CURRENT_SESSION["github_user_id"] = github_user_id
    CURRENT_SESSION["avatar_url"] = avatar_url
    CURRENT_SESSION["resume_username"] = resume_username
    CURRENT_SESSION["verified_at"] = verified_at
    USER_TOKENS[login.lower()] = token

def get_current_token() -> Optional[str]:
    """Get active access token from current session or environment."""
    return CURRENT_SESSION.get("access_token") or GITHUB_TOKEN or None

def get_current_session() -> Dict[str, Any]:
    """Retrieve the current authenticated session details."""
    return CURRENT_SESSION.copy()

def clear_current_session():
    """Clear active session and disconnect."""
    CURRENT_SESSION["access_token"] = GITHUB_TOKEN if GITHUB_TOKEN else None
    CURRENT_SESSION["login"] = None
    CURRENT_SESSION["github_user_id"] = None
    CURRENT_SESSION["avatar_url"] = None
    CURRENT_SESSION["verified_at"] = None
    CURRENT_SESSION["resume_username"] = None
