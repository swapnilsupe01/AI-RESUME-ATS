"""
Unit tests for AI Assistant and Canonical Parser API Routes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_resume_schema():
    response = client.get("/api/ai/resume/schema")
    assert response.status_code == 200
    data = response.json()
    assert "properties" in data
    assert "profile" in data["properties"]
    assert "experience" in data["properties"]
    assert "skills" in data["properties"]


def test_get_sample_resume():
    response = client.get("/api/ai/resume/sample")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["canonical_resume"]["profile"]["name"] == "Alex Chen"
    assert "# Alex Chen" in data["markdown_text"]


def test_parse_to_canvas_with_text():
    sample_text = """# Jordan Lee
**Senior Backend Engineer**
Email: jordan.lee@example.com | Phone: 555-0123
[GitHub](https://github.com/jordanlee/repo)

## Technical Skills
- **Languages & Core:** Python, Go, SQL

## Work Experience
### Senior Backend Engineer — Cloud Corp (2020 – Present)
- Designed resilient microservices architecture in Go and Python.
*Technologies: Python, Go, Docker*
"""
    response = client.post(
        "/api/ai/parse-to-canvas",
        data={"resume_text": sample_text}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["canonical_resume"]["profile"]["name"] == "Jordan Lee"
    assert data["canonical_resume"]["profile"]["email"] == "jordan.lee@example.com"
    assert len(data["canonical_resume"]["experience"]) == 1
    assert data["canonical_resume"]["experience"][0].get("company") == "Cloud Corp"
    assert data["confidence_score"] > 50.0
