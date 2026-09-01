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

def test_linkedin_url_extraction():
    from app.parser.resume_parser import extract_linkedin_urls
    text = "Connect with me at linkedin.com/in/johndoe and https://in.linkedin.com/in/jane-doe-123"
    urls = extract_linkedin_urls(text)
    assert len(urls) == 2
    assert "https://linkedin.com/in/johndoe" in urls

def test_parse_resume_with_additional_links():
    text = "Jane Doe - Python Developer"
    pdf_links = [
        "https://github.com/janedoe/ml-project",
        "https://linkedin.com/in/janedoe",
        "https://janedoe.portfolio.site"
    ]
    parsed = parse_resume(text, additional_links=pdf_links)
    assert "https://github.com/janedoe/ml-project" in parsed["github_urls"]
    assert "https://linkedin.com/in/janedoe" in parsed["linkedin_urls"]
    assert "https://janedoe.portfolio.site" in parsed["portfolio_urls"]
