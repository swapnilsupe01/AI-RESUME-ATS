"""
Unit tests for LinkedIn Verification and Integrations Management API Routes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.evidence.linkedin_oauth import verify_linkedin_identity

client = TestClient(app)


def test_linkedin_connect_endpoint():
    response = client.get("/api/linkedin/connect?resume_name=Alex%20Chen&resume_email=alex@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "auth_url" in data
    assert "state" in data
    assert "oauth_configured" in data


def test_integrations_status_endpoint():
    response = client.get("/api/integrations/status")
    assert response.status_code == 200
    data = response.json()
    assert "github" in data
    assert "linkedin" in data


def test_runtime_configure_github():
    response = client.post(
        "/api/integrations/configure-github",
        data={"token": "test_runtime_token_123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["github_token_configured"] is True


def test_runtime_configure_linkedin():
    response = client.post(
        "/api/integrations/configure-linkedin",
        data={"client_id": "test_linkedin_id", "client_secret": "test_secret"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["linkedin_oauth_configured"] is True


def test_linkedin_identity_verification_matching():
    mock_linkedin_user = {
        "sub": "linkedin_123456",
        "name": "Alex Chen",
        "email": "alex.chen@example.com",
        "picture": "https://media.licdn.com/photo.jpg"
    }

    # Case 1: Matching name & email
    matched = verify_linkedin_identity(mock_linkedin_user, "Alex Chen", "alex.chen@example.com")
    assert matched["is_verified"] is True
    assert matched["status"] == "VERIFIED"
    assert matched["name_matched"] is True
    assert matched["email_matched"] is True
    assert matched["match_score"] == 100.0

    # Case 2: Divergent name
    divergent = verify_linkedin_identity(mock_linkedin_user, "Samantha Miller", "samantha@example.com")
    assert divergent["is_verified"] is True
    assert divergent["status"] == "INCONSISTENCY"
    assert divergent["name_matched"] is False
    assert divergent["email_matched"] is False


def test_linkedin_post_and_unverified_baseline_score():
    from app.evidence.identity_verifier import _signal_linkedin_post_github_link
    from app.evidence.linkedin_analyzer import _unverified_response

    score, note = _signal_linkedin_post_github_link([], "testuser")
    assert score == 60.0
    assert "baseline 60% score applied" in note

    unverified = _unverified_response("No token")
    assert unverified["heuristic_score"] == 60.0

