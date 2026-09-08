"""
GitHub Intelligence API Routes.
Provides endpoints for GitHub OAuth authorization, identity ownership verification,
real GraphQL contribution calendar fetching, repository activity, and provenance tracking.
"""
from fastapi import APIRouter, HTTPException, Query, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from typing import Optional, Dict, Any

from app.github.oauth_service import (
    generate_oauth_url,
    validate_oauth_state,
    exchange_code_for_token,
    get_current_session,
    clear_current_session,
    GITHUB_CLIENT_ID
)
from app.github.identity_service import (
    fetch_authenticated_user,
    verify_ownership_comparison,
    check_current_ownership
)
from app.github.contribution_service import get_verified_github_contributions
from app.github.repository_service import format_repository_evidence

router = APIRouter(prefix="/api/github", tags=["GitHub Real Contribution Intelligence"])

@router.get("/connect")
async def connect_github(
    resume_username: Optional[str] = Query(None, description="Extracted resume GitHub username"),
    redirect: bool = Query(False, description="Whether to redirect immediately to GitHub OAuth URL")
):
    """
    Initiate GitHub OAuth connection for Ownership Verification.
    """
    auth_url, state = generate_oauth_url(resume_username=resume_username)

    if redirect and GITHUB_CLIENT_ID:
        return RedirectResponse(url=auth_url)

    return {
        "auth_url": auth_url,
        "state": state,
        "oauth_configured": bool(GITHUB_CLIENT_ID),
        "message": (
            "Ready for GitHub OAuth authorization."
            if GITHUB_CLIENT_ID
            else "GitHub Client ID not configured in .env. You can connect using a GitHub Token or Personal Access Token (PAT)."
        )
    }

@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    Handle GitHub OAuth callback. Exchanges code for token and verifies ownership.
    """
    if error:
        return HTMLResponse(
            f"""<html><body><script>
            window.opener && window.opener.postMessage({{type: 'GITHUB_AUTH_ERROR', error: '{error}: {error_description}'}}, '*');
            window.close();
            </script><p>GitHub Authorization failed: {error_description}. You can close this window.</p></body></html>"""
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state in OAuth callback.")

    state_data = validate_oauth_state(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state token.")

    token = await exchange_code_for_token(code)
    if not token:
        return HTMLResponse(
            """<html><body><script>
            window.opener && window.opener.postMessage({type: 'GITHUB_AUTH_ERROR', error: 'Failed to exchange code for access token.'}, '*');
            window.close();
            </script><p>Token exchange failed. You can close this window.</p></body></html>"""
        )

    # Fetch identity
    user_info = await fetch_authenticated_user(token)
    if not user_info:
        return HTMLResponse(
            """<html><body><script>
            window.opener && window.opener.postMessage({type: 'GITHUB_AUTH_ERROR', error: 'Could not fetch identity from GitHub API.'}, '*');
            window.close();
            </script><p>Identity verification failed. You can close this window.</p></body></html>"""
        )

    resume_user = state_data.get("resume_username")
    status = verify_ownership_comparison(
        authenticated_login=user_info.get("login", ""),
        authenticated_id=user_info.get("id", 0),
        authenticated_avatar=user_info.get("avatar_url"),
        resume_username=resume_user,
        token=token
    )

    # Close popup and notify parent window via postMessage
    return HTMLResponse(
        f"""<!DOCTYPE html>
        <html>
        <head><title>GitHub Ownership Verified</title></head>
        <body style="background:#0b0f19;color:#fff;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;">
          <div style="text-align:center;padding:24px;border:1px solid rgba(0,240,255,0.3);border-radius:12px;background:rgba(18,24,38,0.9);">
            <h2 style="color:#00f0ff;margin:0 0 12px;">GitHub Ownership Verified!</h2>
            <p>Authenticated as <strong>@{status.login}</strong> (ID: {status.github_user_id})</p>
            <p style="color:#8892b0;font-size:12px;">This window will close automatically...</p>
          </div>
          <script>
            try {{
              if (window.opener) {{
                window.opener.postMessage({{
                  type: 'GITHUB_AUTH_SUCCESS',
                  status: {status.json()}
                }}, '*');
              }}
            }} catch(e) {{}}
            setTimeout(() => window.close(), 1200);
          </script>
        </body>
        </html>"""
    )

@router.post("/verify-token")
async def verify_token_direct(
    token: str = Form(..., description="GitHub Personal Access Token or OAuth token"),
    resume_username: Optional[str] = Form(None, description="Candidate resume GitHub username")
):
    """
    Directly verify GitHub ownership using a token (e.g. PAT / fine-grained token).
    Enables instant verification without public OAuth callback setup.
    """
    clean_token = token.strip()
    if not clean_token:
        raise HTTPException(status_code=400, detail="Token cannot be empty.")

    user_info = await fetch_authenticated_user(clean_token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid GitHub token or insufficient permissions.")

    status = verify_ownership_comparison(
        authenticated_login=user_info.get("login", ""),
        authenticated_id=user_info.get("id", 0),
        authenticated_avatar=user_info.get("avatar_url"),
        resume_username=resume_username.strip() if resume_username else None,
        token=clean_token
    )

    return status

@router.get("/status")
async def get_ownership_status(
    resume_username: Optional[str] = Query(None, description="Resume extracted GitHub username")
):
    """
    Get current GitHub ownership verification status.
    """
    status = await check_current_ownership(resume_username=resume_username)
    return status

@router.get("/profile")
async def get_github_profile():
    """
    Get authenticated user profile details.
    """
    session = get_current_session()
    token = session.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="No active GitHub authentication.")

    user_info = await fetch_authenticated_user(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="Could not retrieve profile. Token may be expired.")

    return user_info

@router.get("/contributions")
async def get_contributions(
    username: str = Query(..., description="GitHub username to inspect"),
    year: Optional[str] = Query(None, description="Specific year e.g. 2026, or empty for latest")
):
    """
    Fetch real GitHub contribution calendar, active years, totals, and repository breakdown.
    Strictly uses official GitHub GraphQL API.
    """
    clean_user = username.strip().lstrip("@")
    payload = await get_verified_github_contributions(username=clean_user, selected_year=year)
    return payload

@router.get("/contributions/{year}")
async def get_contributions_for_year(
    year: str,
    username: str = Query(..., description="GitHub username to inspect")
):
    """
    Fetch real GitHub contribution calendar for a specific selected year (e.g. 2024).
    """
    clean_user = username.strip().lstrip("@")
    payload = await get_verified_github_contributions(username=clean_user, selected_year=year)
    return payload

@router.get("/repositories")
async def get_contributed_repositories(
    username: str = Query(..., description="GitHub username to inspect"),
    year: Optional[str] = Query(None, description="Specific year")
):
    """
    Retrieve repository-grouped contribution evidence from GraphQL commitContributionsByRepository.
    """
    clean_user = username.strip().lstrip("@")
    payload = await get_verified_github_contributions(username=clean_user, selected_year=year)
    evidence = format_repository_evidence(payload.top_repositories, has_restricted=payload.has_restricted_contributions)
    return evidence

@router.get("/activity")
async def get_contribution_activity(
    username: str = Query(..., description="GitHub username to inspect")
):
    """
    Multi-year real activity timeline originating strictly from GitHub contribution collections.
    """
    clean_user = username.strip().lstrip("@")
    payload = await get_verified_github_contributions(username=clean_user)

    timeline = []
    for y in payload.years_active:
        timeline.append({
            "year": y,
            "evidence": f"Recorded authentic GitHub contributions in {y}",
            "source": "github_graphql_api"
        })

    return {
        "username": clean_user,
        "timeline": timeline,
        "source": "github_graphql_api",
        "retrieved_at": payload.retrieved_at
    }

@router.post("/disconnect")
async def disconnect_github():
    """
    Disconnect GitHub account and clear session.
    """
    clear_current_session()
    return {"status": "disconnected", "message": "GitHub account session cleared."}
