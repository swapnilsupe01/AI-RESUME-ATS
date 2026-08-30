"""
Unit tests for Public Evidence Verification.
"""
import pytest
from app.evidence.url_extractor import parse_github_url, extract_project_evidence_urls
from app.evidence.project_verifier import verify_project_claims

def test_parse_github_url():
    parsed = parse_github_url("https://github.com/swapnilsupe01/ai-resume-ats")
    assert parsed is not None
    assert parsed["type"] == "repository"
    assert parsed["owner"] == "swapnilsupe01"
    assert parsed["repo"] == "ai-resume-ats"

def test_verify_project_claims():
    claims = [{
        "project_title": "AI Resume ATS",
        "technologies": ["python", "fastapi"],
        "claims": [
            {"claim_type": "Skill", "claim": "Python"},
            {"claim_type": "Skill", "claim": "FastAPI"},
            {"claim_type": "Skill", "claim": "AWS Cloud"}
        ],
        "urls": ["https://github.com/swapnilsupe01/ai-resume-ats"]
    }]

    github_evidence = [{
        "repo_name": "ai-resume-ats",
        "full_name": "swapnilsupe01/ai-resume-ats",
        "technologies": ["Python", "FastAPI", "Docker"],
        "languages": ["Python"],
        "description": "AI Resume ATS system built with Python and FastAPI.",
        "evidence_snippets": ["Python backend with FastAPI"]
    }]

    res = verify_project_claims(claims, github_evidence, [])
    assert res["total_claims_analyzed"] == 3
    assert res["verified_claims_count"] >= 2
    assert res["overall_evidence_score"] > 50.0
