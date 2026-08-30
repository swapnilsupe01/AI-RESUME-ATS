"""
Unit tests for Exact & Semantic Skill Matching.
"""
import pytest
from app.matching.skill_matcher import match_skills_comprehensive

def test_skill_matching_exact_and_semantic():
    candidate_skills = ["python", "fastapi", "scikit-learn", "docker"]
    jd_skills = ["python", "fastapi", "machine learning", "kubernetes", "aws"]

    res = match_skills_comprehensive(candidate_skills, jd_skills)
    
    assert "Python" in res["matched_skills"]
    assert "Fastapi" in res["matched_skills"]
    assert res["exact_matched_count"] >= 2
    assert res["skill_match_score"] > 0
    assert "Aws" in res["missing_skills"]
