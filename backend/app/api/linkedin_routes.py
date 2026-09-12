"""
LinkedIn Intelligence & Official OpenID Verification API Routes.
Complies with official LinkedIn OpenID Connect identity verification standards.
"""
from fastapi import APIRouter, HTTPException, Query, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from typing import Optional, Dict, Any

from app.evidence.linkedin_oauth import (
    generate_linkedin_oauth_url,
    validate_linkedin_oauth_state,
    exchange_linkedin_code,
    fetch_linkedin_userinfo,
    verify_linkedin_identity,
    is_linkedin_configured,
    CURRENT_LINKEDIN_SESSION
)

router = APIRouter(prefix="/api/linkedin", tags=["LinkedIn Official Verification"])


@router.get("/connect")
async def connect_linkedin(
    resume_name: Optional[str] = Query(None, description="Resume candidate name"),
    resume_email: Optional[str] = Query(None, description="Resume candidate email"),
    redirect: bool = Query(False, description="Redirect immediately to LinkedIn OAuth URL")
):
    """
    Initiate official LinkedIn OpenID Connect authorization.
    """
    auth_url, state = generate_linkedin_oauth_url(resume_name=resume_name, resume_email=resume_email)
    configured = is_linkedin_configured()

    if redirect and configured:
        return RedirectResponse(url=auth_url)

    return {
        "auth_url": auth_url,
        "state": state,
        "oauth_configured": configured,
        "message": (
            "Ready for official LinkedIn authorization."
            if configured
            else "LINKEDIN_CLIENT_ID not configured in .env. You can configure credentials in Settings or verify via Token."
        )
    }


@router.get("/callback")
async def linkedin_oauth_callback(
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    error_description: Optional[str] = Query(None)
):
    """
    Handle official LinkedIn OAuth callback and verify identity consistency.
    """
    if error:
        return HTMLResponse(
            f"""<html><body><script>
            window.opener && window.opener.postMessage({{type: 'LINKEDIN_AUTH_ERROR', error: '{error}: {error_description}'}}, '*');
            window.close();
            </script><p>LinkedIn Authorization failed: {error_description}. You can close this window.</p></body></html>"""
        )

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state in LinkedIn callback.")

    state_data = validate_linkedin_oauth_state(state)
    if not state_data:
        raise HTTPException(status_code=400, detail="Invalid or expired LinkedIn OAuth state token.")

    token = await exchange_linkedin_code(code)
    if not token:
        return HTMLResponse(
            """<html><body><script>
            window.opener && window.opener.postMessage({type: 'LINKEDIN_AUTH_ERROR', error: 'Failed to exchange code for LinkedIn token.'}, '*');
            window.close();
            </script><p>Token exchange failed. You can close this window.</p></body></html>"""
        )

    userinfo = await fetch_linkedin_userinfo(token)
    if not userinfo:
        return HTMLResponse(
            """<html><body><script>
            window.opener && window.opener.postMessage({type: 'LINKEDIN_AUTH_ERROR', error: 'Could not fetch user profile from LinkedIn API.'}, '*');
            window.close();
            </script><p>Profile fetch failed. You can close this window.</p></body></html>"""
        )

    resume_name = state_data.get("resume_name")
    resume_email = state_data.get("resume_email")
    verification = verify_linkedin_identity(userinfo, resume_name, resume_email)

    import json
    return HTMLResponse(
        f"""<html>
        <body style="background:#020b18;color:#e2eaf7;font-family:sans-serif;display:flex;align-items:center;justify-content:center;height:100vh;">
          <div style="text-align:center;padding:2rem;border:1px solid rgba(0,229,255,0.3);border-radius:1rem;background:#0a1e33;">
            <h2 style="color:#39ff8f;margin-bottom:0.5rem;">✓ LinkedIn Identity Verified!</h2>
            <p>Authenticated as <strong>{verification.get('name')}</strong></p>
            <p style="color:#94a3b8;font-size:12px;">Closing this window...</p>
          </div>
          <script>
            try {{
              if (window.opener) {{
                window.opener.postMessage({{
                  type: 'LINKEDIN_AUTH_SUCCESS',
                  status: {json.dumps(verification)}
                }}, '*');
              }}
            }} catch(e) {{}}
            setTimeout(() => window.close(), 1200);
          </script>
        </body>
        </html>"""
    )


@router.get("/status")
async def get_linkedin_status():
    """
    Get current LinkedIn verification status.
    """
    return JSONResponse(content=CURRENT_LINKEDIN_SESSION)


@router.post("/verify-token")
async def verify_linkedin_token(
    token: str = Form(..., description="LinkedIn Access Token"),
    resume_name: Optional[str] = Form(None),
    resume_email: Optional[str] = Form(None)
):
    """
    Directly verify identity using an existing LinkedIn Access Token.
    """
    clean_token = token.strip()
    if not clean_token:
        raise HTTPException(status_code=400, detail="Token cannot be empty.")

    userinfo = await fetch_linkedin_userinfo(clean_token)
    if not userinfo:
        raise HTTPException(status_code=401, detail="Invalid LinkedIn access token or expired session.")

    verification = verify_linkedin_identity(userinfo, resume_name, resume_email)
    return JSONResponse(content=verification)
