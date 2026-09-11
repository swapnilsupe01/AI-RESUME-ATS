"""
Integrations & Credentials Management API.
Allows runtime verification, configuration, and persistence of GitHub and LinkedIn OAuth / API credentials.
"""
from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
from typing import Optional, Dict
import os

from app.github import oauth_service as gh_oauth
from app.evidence import linkedin_oauth as li_oauth

router = APIRouter(prefix="/api/integrations", tags=["Integrations & Credentials"])

# Path to backend/.env
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_ENV_PATH = os.path.join(_BACKEND_DIR, ".env")


def _mask_secret(val: Optional[str]) -> str:
    """Return masked representation of sensitive credential."""
    if not val:
        return ""
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"


def _save_to_env(updates: Dict[str, str]):
    """Persist key/value updates to .env file preserving existing comments."""
    try:
        lines = []
        if os.path.isfile(_ENV_PATH):
            with open(_ENV_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

        existing_keys = set()
        new_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.split("=", 1)[0].strip()
                if key in updates:
                    new_lines.append(f"{key}={updates[key]}\n")
                    existing_keys.add(key)
                    continue
            new_lines.append(line)

        # Append any new keys not already in the file
        for k, v in updates.items():
            if k not in existing_keys:
                if new_lines and not new_lines[-1].endswith("\n"):
                    new_lines.append("\n")
                new_lines.append(f"{k}={v}\n")

        with open(_ENV_PATH, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"[ENV SAVE ERROR]: {e}")


@router.get("/status")
async def get_integrations_status():
    """Returns the live configuration status of all connected services."""
    gh_token = gh_oauth.get_current_token()
    return {
        "github": {
            "oauth_configured": bool(gh_oauth.GITHUB_CLIENT_ID),
            "token_configured": bool(gh_token),
            "client_id_masked": _mask_secret(gh_oauth.GITHUB_CLIENT_ID),
            "token_masked": _mask_secret(gh_token),
            "redirect_uri": gh_oauth.GITHUB_REDIRECT_URI,
            "session_active": bool(gh_oauth.CURRENT_SESSION.get("login")),
            "session_user": gh_oauth.CURRENT_SESSION.get("login")
        },
        "linkedin": {
            "oauth_configured": li_oauth.is_linkedin_configured(),
            "client_id_masked": _mask_secret(li_oauth.LINKEDIN_CLIENT_ID),
            "redirect_uri": li_oauth.LINKEDIN_REDIRECT_URI,
            "session_active": bool(li_oauth.CURRENT_LINKEDIN_SESSION.get("is_verified")),
            "session_user": li_oauth.CURRENT_LINKEDIN_SESSION.get("name")
        }
    }


@router.post("/configure-github")
async def configure_github(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    token: Optional[str] = Form(None)
):
    """Dynamically configure GitHub OAuth or Token credentials in runtime memory and .env."""
    env_updates: Dict[str, str] = {}

    if client_id is not None:
        clean_cid = client_id.strip()
        gh_oauth.GITHUB_CLIENT_ID = clean_cid
        os.environ["GITHUB_CLIENT_ID"] = clean_cid
        env_updates["GITHUB_CLIENT_ID"] = clean_cid

    if client_secret is not None:
        clean_secret = client_secret.strip()
        gh_oauth.GITHUB_CLIENT_SECRET = clean_secret
        os.environ["GITHUB_CLIENT_SECRET"] = clean_secret
        env_updates["GITHUB_CLIENT_SECRET"] = clean_secret

    if token is not None:
        clean_token = token.strip()
        gh_oauth.GITHUB_TOKEN = clean_token
        os.environ["GITHUB_TOKEN"] = clean_token
        gh_oauth.CURRENT_SESSION["access_token"] = clean_token if clean_token else None
        env_updates["GITHUB_TOKEN"] = clean_token

    if env_updates:
        _save_to_env(env_updates)

    return {
        "status": "success",
        "message": "GitHub credentials updated and saved.",
        "github_oauth_configured": bool(gh_oauth.GITHUB_CLIENT_ID),
        "github_token_configured": bool(gh_oauth.GITHUB_TOKEN)
    }


@router.post("/configure-linkedin")
async def configure_linkedin(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None)
):
    """Dynamically configure LinkedIn OAuth credentials in runtime memory and .env."""
    env_updates: Dict[str, str] = {}

    if client_id is not None:
        clean_cid = client_id.strip()
        li_oauth.LINKEDIN_CLIENT_ID = clean_cid
        os.environ["LINKEDIN_CLIENT_ID"] = clean_cid
        env_updates["LINKEDIN_CLIENT_ID"] = clean_cid

    if client_secret is not None:
        clean_secret = client_secret.strip()
        li_oauth.LINKEDIN_CLIENT_SECRET = clean_secret
        os.environ["LINKEDIN_CLIENT_SECRET"] = clean_secret
        env_updates["LINKEDIN_CLIENT_SECRET"] = clean_secret

    if env_updates:
        _save_to_env(env_updates)

    return {
        "status": "success",
        "message": "LinkedIn credentials updated and saved.",
        "linkedin_oauth_configured": li_oauth.is_linkedin_configured()
    }

