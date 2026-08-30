"""
Unit tests for ATS and Evidence Scoring.
"""
import pytest
from app.scoring.ats_scorer import calculate_job_match_score
from app.scoring.evidence_scorer import calculate_evidence_score

def test_job_match_score_calculation():
    resume_text = "Python developer with experience in FastAPI, scikit-learn, SQL, and Docker."
    jd_text = "Looking for a Python Developer with FastAPI and SQL knowledge."

    score_res = calculate_job_match_score(resume_text, jd_text)
    assert score_res["job_match_score"] > 50
    assert "Python" in score_res["matched_skills"]
    assert "Fastapi" in score_res["matched_skills"]

def test_evidence_score_calculation():
    mock_verification = {
        "overall_evidence_score": 85.0,
        "github_repositories_analyzed": [{"name": "repo1"}],
        "portfolios_analyzed": [],
        "inconsistencies": []
    }
    
    score_res = calculate_evidence_score(mock_verification, has_github=True, has_portfolio=False)
    assert score_res["evidence_score"] >= 80
    assert score_res["is_evidence_available"] is True
