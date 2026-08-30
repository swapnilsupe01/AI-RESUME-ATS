"""
Unit tests for PDF & Resume Parsing.
"""
import pytest
from app.parser.resume_parser import parse_resume, extract_github_urls, extract_portfolio_urls
from app.utils.skills import extract_skills

def test_resume_parser_contact_extraction():
    sample_text = """
    JOHN DOE
    Email: john.doe@example.com | Phone: 123-456-7890
    GitHub: https://github.com/johndoe/sample-project
    Portfolio: https://johndoe.dev

    SKILLS:
    Python, FastAPI, Docker, SQL
    """
    parsed = parse_resume(sample_text)
    assert parsed["candidate_name"] == "John Doe"
    assert parsed["email"] == "john.doe@example.com"
    assert "https://github.com/johndoe/sample-project" in parsed["github_urls"]
    assert "https://johndoe.dev" in parsed["portfolio_urls"]
    assert "python" in parsed["extracted_skills"]
    assert "fastapi" in parsed["extracted_skills"]

def test_github_url_extraction():
    text = "Find my work at github.com/user/my-repo and https://github.com/user/another-project"
    urls = extract_github_urls(text)
    assert len(urls) == 2
    assert "https://github.com/user/my-repo" in urls
