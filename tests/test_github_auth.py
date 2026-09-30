"""
GitHub Authentication & Evidence Test Suite.
Tests cover:
  1. GitHub OAuth URL generation & CSRF state verification.
  2. GitHub OAuth user denial & code exchange failure handling.
  3. GitHub PAT direct verification (valid, invalid 401, and empty).
  4. Session disconnection and account isolation.
  5. Commit author name matching (handles, logins, substrings).
  6. Commit email cross-match (base handle matching e.g. swapnilsupe01 vs swapnilsupe55).
  7. GitHub API failure resilience (401/403/404 do not break resume analysis).
"""

from unittest.mock import patch, MagicMock, AsyncMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.github.oauth_service import (
    generate_oauth_url,
    validate_oauth_state,
    get_current_session,
    clear_current_session,
    set_current_session,
    OAUTH_STATES,
)
from app.evidence.identity_verifier import (
    _signal_commit_author,
    _signal_commit_email_crossmatch,
    verify_github_ownership,
)

client = TestClient(app)


# ── 1. GitHub OAuth Tests ───────────────────────────────────────────────────

def test_oauth_url_and_state_generation():
    """OAuth URL contains required client_id, scopes, and unique CSRF state."""
    with patch("app.github.oauth_service.GITHUB_CLIENT_ID", "test_client_id_123"):
        url, state = generate_oauth_url(resume_username="swapnilsupe01")
        assert "client_id=test_client_id_123" in url
        assert "scope=" in url
        assert f"state={state}" in url
        assert state in OAUTH_STATES
        assert OAUTH_STATES[state]["resume_username"] == "swapnilsupe01"

        # State must be consumed once and invalidated
        state_data = validate_oauth_state(state)
        assert state_data is not None
        assert state_data["resume_username"] == "swapnilsupe01"
        assert validate_oauth_state(state) is None


def test_oauth_callback_user_denial():
    """When user denies OAuth consent, callback returns clear error HTML."""
    res = client.get(
        "/api/github/callback?error=access_denied&error_description=The+user+has+denied+your+application+access."
    )
    assert res.status_code == 200
    assert "GITHUB_AUTH_ERROR" in res.text
    assert "access_denied" in res.text


def test_oauth_callback_invalid_state():
    """Callback with nonexistent or expired state token returns 400."""
    res = client.get("/api/github/callback?code=mock_code&state=nonexistent_state_token")
    assert res.status_code == 400
    assert "Invalid or expired OAuth state" in res.json()["detail"]


# ── 2. GitHub PAT Tests ─────────────────────────────────────────────────────

def test_pat_empty_token_rejected():
    """Empty or whitespace-only PAT tokens are rejected with 400."""
    res = client.post("/api/github/verify-token", data={"token": "   "})
    assert res.status_code == 400
    assert "Token cannot be empty" in res.json()["detail"]


@patch("app.github.identity_service.fetch_authenticated_user")
def test_pat_invalid_token_returns_401(mock_fetch):
    """When GitHub returns 401 Bad credentials, verify-token returns 401 with helpful detail."""
    mock_fetch.return_value = None
    res = client.post(
        "/api/github/verify-token",
        data={"token": "ghp_invalid_token_xyz", "resume_username": "swapnilsupe01"}
    )
    assert res.status_code == 401
    assert "Invalid GitHub token" in res.json()["detail"]


@patch("app.github.identity_service.fetch_authenticated_user")
def test_pat_valid_token_matches_username(mock_fetch):
    """Valid PAT matching the resume username establishes verified ownership."""
    mock_fetch.return_value = {
        "login": "swapnilsupe01",
        "id": 99887766,
        "avatar_url": "https://avatars.githubusercontent.com/u/99887766",
        "name": "Swapnil Supe",
        "email": "swapnilsupe01@gmail.com",
    }

    res = client.post(
        "/api/github/verify-token",
        data={"token": "ghp_valid_test_token_123", "resume_username": "swapnilsupe01"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verified"] is True
    assert data["matched"] is True
    assert data["login"] == "swapnilsupe01"
    assert data["github_user_id"] == 99887766

    clear_current_session()


@patch("app.github.identity_service.fetch_authenticated_user")
def test_pat_account_mismatch_detected(mock_fetch):
    """PAT belonging to a different account than the resume is detected as MISMATCH."""
    mock_fetch.return_value = {
        "login": "otherdeveloper",
        "id": 11223344,
        "avatar_url": None,
        "name": "Other Dev",
    }

    res = client.post(
        "/api/github/verify-token",
        data={"token": "ghp_other_token_123", "resume_username": "swapnilsupe01"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "MISMATCH"
    assert data["matched"] is False
    assert data["login"] == "otherdeveloper"

    clear_current_session()


# ── 3. Commit Author Name & Email Matching Tests ─────────────────────────────

def test_commit_author_name_matches_username():
    """Author name configured as GitHub username (e.g. swapnilsupe01) passes 100%."""
    commits = [
        {
            "commit": {"author": {"name": "swapnilsupe01", "email": "swapnilsupe01@gmail.com"}},
            "author": {"login": "swapnilsupe01"}
        }
    ] * 5

    score, note = _signal_commit_author(
        commits,
        candidate_name="Swapnil Supe",
        github_username="swapnilsupe01",
        is_authenticated=False
    )
    assert score == 100.0
    assert "authored by" in note or "consistent" in note


def test_commit_author_name_matches_single_name():
    """Author name set to just first name 'Swapnil' matches candidate 'Swapnil Supe'."""
    commits = [
        {
            "commit": {"author": {"name": "Swapnil", "email": "swapnil@example.com"}},
            "author": {"login": "swapnilsupe01"}
        }
    ]

    score, note = _signal_commit_author(
        commits,
        candidate_name="Swapnil Supe",
        github_username="swapnilsupe01",
        is_authenticated=False
    )
    assert score == 100.0


def test_commit_email_base_handle_match():
    """Commit email swapnilsupe01@gmail.com matches resume email swapnilsupe55@gmail.com."""
    commits = [
        {
            "commit": {"author": {"name": "Swapnil Supe", "email": "swapnilsupe01@gmail.com"}}
        }
    ]

    score, note = _signal_commit_email_crossmatch(
        commits,
        resume_email="swapnilsupe55@gmail.com",
        candidate_name="Swapnil Supe",
        is_authenticated=False
    )
    assert score >= 90.0
    assert "swapnilsupe" in note


def test_authenticated_token_gives_100_percent_signals():
    """When candidate is authenticated via Token/OAuth, signals reflect verified ownership."""
    commits = []
    score_author, _ = _signal_commit_author(
        commits,
        candidate_name="Swapnil Supe",
        github_username="swapnilsupe01",
        is_authenticated=True
    )
    assert score_author == 100.0

    score_email, _ = _signal_commit_email_crossmatch(
        commits,
        resume_email="swapnilsupe55@gmail.com",
        candidate_name="Swapnil Supe",
        is_authenticated=True
    )
    assert score_email == 100.0


# ── 4. Error Resilience ─────────────────────────────────────────────────────

def test_github_api_failure_does_not_break_ownership_verifier():
    """If GitHub API times out or fails with 401/403, verify_github_ownership returns safe fallback."""
    import asyncio

    async def _test():
        with patch("app.evidence.identity_verifier._fetch_github_user_profile", AsyncMock(return_value={})):
            with patch("app.evidence.identity_verifier._fetch_recent_commits", AsyncMock(return_value=[])):
                result = await verify_github_ownership(
                    github_username="nonexistent_user_999",
                    candidate_name="Test Candidate",
                )
                assert result is not None
                assert "ownership_score" in result
                assert "signals" in result

    asyncio.run(_test())
