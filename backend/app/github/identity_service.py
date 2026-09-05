"""
GitHub Authenticated Identity & Ownership Verification Service.
Fetches immutable GitHub ID and login from official endpoint (GET https://api.github.com/user),
compares authenticated identity against resume extracted GitHub handle,
and records verification state in SQLite.
"""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.github.github_models import GitHubOwnershipStatus
from app.github.db import save_verified_account, get_verified_account
from app.github.oauth_service import set_current_session, get_current_session

async def fetch_authenticated_user(token: str) -> Optional[Dict[str, Any]]:
    """
    Fetch authenticated GitHub user identity using official REST endpoint:
    GET https://api.github.com/user
    """
    if not token:
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Resume-ATS/2.0"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get("https://api.github.com/user", headers=headers)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[Identity Service Notice]: GitHub /user responded {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[Identity Service Error]: {e}")

    return None

def verify_ownership_comparison(
    authenticated_login: str,
    authenticated_id: int,
    authenticated_avatar: Optional[str],
    resume_username: Optional[str],
    token: Optional[str] = None
) -> GitHubOwnershipStatus:
    """
    Compare authenticated GitHub identity with resume username.
    Resume account: github.com/username
    Authenticated account: login = username, id = 123456789
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    norm_auth = authenticated_login.strip().lower()
    norm_resume = resume_username.strip().lower() if resume_username else ""

    if not norm_resume:
        # Authenticated, but no resume username provided yet
        if token:
            set_current_session(token, authenticated_login, authenticated_id, authenticated_avatar, None, now_iso)
        return GitHubOwnershipStatus(
            verified=True,
            status="VERIFIED",
            login=authenticated_login,
            github_user_id=authenticated_id,
            avatar_url=authenticated_avatar,
            resume_username=None,
            matched=True,
            verified_at=now_iso,
            message=f"✓ GitHub Identity Authenticated: @{authenticated_login} (ID: {authenticated_id})"
        )

    matched = (norm_auth == norm_resume)

    if matched:
        # Exact match
        if token:
            set_current_session(token, authenticated_login, authenticated_id, authenticated_avatar, resume_username, now_iso)
        save_verified_account(
            github_user_id=authenticated_id,
            login=authenticated_login,
            profile_url=f"https://github.com/{authenticated_login}",
            ownership_verified=True,
            verified_at=now_iso
        )
        return GitHubOwnershipStatus(
            verified=True,
            status="VERIFIED",
            login=authenticated_login,
            github_user_id=authenticated_id,
            avatar_url=authenticated_avatar,
            resume_username=resume_username,
            matched=True,
            verified_at=now_iso,
            message=f"✓ GitHub Ownership Verified: @{authenticated_login} (ID: {authenticated_id})"
        )
    else:
        # Accounts don't match: warn user honestly, do not treat automatically as fraud
        if token:
            set_current_session(token, authenticated_login, authenticated_id, authenticated_avatar, resume_username, now_iso)
        save_verified_account(
            github_user_id=authenticated_id,
            login=authenticated_login,
            profile_url=f"https://github.com/{authenticated_login}",
            ownership_verified=False,
            verified_at=now_iso
        )
        return GitHubOwnershipStatus(
            verified=False,
            status="MISMATCH",
            login=authenticated_login,
            github_user_id=authenticated_id,
            avatar_url=authenticated_avatar,
            resume_username=resume_username,
            matched=False,
            verified_at=now_iso,
            message=(
                f"⚠️ GitHub Ownership Not Verified: Resume account: github.com/{resume_username} "
                f"vs Authenticated account: github.com/{authenticated_login} (ID: {authenticated_id})"
            )
        )

async def check_current_ownership(resume_username: Optional[str] = None) -> GitHubOwnershipStatus:
    """Check current ownership verification state."""
    session = get_current_session()
    token = session.get("access_token")
    login = session.get("login")
    gh_id = session.get("github_user_id")
    avatar = session.get("avatar_url")
    verified_at = session.get("verified_at")

    if not token:
        return GitHubOwnershipStatus(
            verified=False,
            status="UNVERIFIED",
            resume_username=resume_username,
            matched=False,
            message="GitHub Ownership Not Verified. Connect your GitHub account to retrieve verified contribution data."
        )

    # If login is already in session, compare
    if login and gh_id:
        return verify_ownership_comparison(login, gh_id, avatar, resume_username, token)

    # If we have a token but haven't fetched identity yet, fetch from GitHub
    user_data = await fetch_authenticated_user(token)
    if user_data:
        return verify_ownership_comparison(
            authenticated_login=user_data.get("login", ""),
            authenticated_id=user_data.get("id", 0),
            authenticated_avatar=user_data.get("avatar_url"),
            resume_username=resume_username,
            token=token
        )

    return GitHubOwnershipStatus(
        verified=False,
        status="ERROR",
        resume_username=resume_username,
        matched=False,
        message="GitHub API request failed: Unable to verify token identity. Please reconnect."
    )
