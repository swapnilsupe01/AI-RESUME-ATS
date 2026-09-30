"""
Tests for Upgrade CV / EnhanceCV AI module:
- Resume RAG Engine
- CV Diagnostics API
- Full CV Transformation API (with anti-hallucination constraint)
- ATS-Compliant PDF Generation
- Before vs After ATS Score Comparison API
"""
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ai.rag_engine import rag_engine
from app.parser.pdf_generator import pdf_generator
import pymupdf as fitz

client = TestClient(app)


def test_rag_sentence_restructuring_anti_hallucination():
    """Verify that weak sentences are restructured without adding unmentioned tools."""
    weak_bullet = "worked on building web services and did testing"
    candidate_tools = ["Python", "FastAPI"]
    restructured, changes = rag_engine.restructure_sentence(weak_bullet, candidate_tools)

    assert "worked on" not in restructured.lower()
    assert len(changes) > 0
    assert restructured.endswith(".")
    # Ensure unmentioned tools like Kubernetes/Rust are not hallucinated
    assert "Kubernetes" not in restructured
    assert "Rust" not in restructured


def test_pdf_generator_produces_valid_ats_pdf():
    """Verify ATS PDF generator outputs valid machine-readable PDF bytes."""
    sample_resume = {
        "candidate_name": "Test Engineer",
        "email": "test@example.com",
        "phone": "(555) 123-4567",
        "github_url": "https://github.com/testengineer",
        "summary": "Experienced software engineer with expertise in Python and REST APIs.",
        "skills": ["Python", "FastAPI", "Docker", "SQL"],
        "experience": [
            {
                "title": "Software Developer",
                "company": "Tech Corp",
                "dates": "2022 - 2024",
                "bullets": [
                    "Architected high-throughput REST APIs using FastAPI.",
                    "Containerized application environments using Docker."
                ]
            }
        ],
        "projects": [
            {
                "name": "AI Resume Scanner",
                "tech_stack": ["Python", "FastAPI"],
                "bullets": ["Engineered semantic parser using PyMuPDF."]
            }
        ],
        "education": [
            {
                "degree": "B.S. Computer Science",
                "institution": "State University",
                "year": "2022"
            }
        ]
    }

    pdf_bytes = pdf_generator.generate_pdf(sample_resume)
    assert len(pdf_bytes) > 500

    # Verify PyMuPDF can open and extract text back cleanly
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    assert doc.page_count >= 1
    extracted_text = doc[0].get_text()
    assert "TEST ENGINEER" in extracted_text
    assert "test@example.com" in extracted_text
    assert "FastAPI" in extracted_text
    doc.close()


def test_diagnose_cv_endpoint():
    """Test POST /api/ai/diagnose endpoint."""
    sample_resume = """
    John Doe
    Email: john@example.com
    Experience:
    • worked on backend services
    • helped with database queries
    """
    sample_jd = """
    Senior Python Engineer. Required skills: Python, FastAPI, Docker, Kubernetes, SQL.
    """

    res = client.post(
        "/api/ai/diagnose",
        data={"resume_text": sample_resume, "jd_text": sample_jd}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "cv_health_score" in data
    assert "issues" in data
    assert len(data["issues"]) > 0
    # Should catch weak verbs and missing skills
    categories = [i["category"] for i in data["issues"]]
    assert "Skill Coverage" in categories or "Impact & Action Verbs" in categories


def test_transform_cv_endpoint():
    """Test POST /api/ai/transform-cv endpoint."""
    canonical_resume = {
        "candidate_name": "Swapnil Supe",
        "email": "swapnil@example.com",
        "skills": ["Python", "FastAPI", "Docker"],
        "experience": [
            {
                "title": "Software Intern",
                "company": "AI Labs",
                "bullets": ["worked on building machine learning models with FastAPI"]
            }
        ],
        "projects": []
    }
    sample_jd = "Machine Learning Engineer. Python, FastAPI, Machine Learning."

    res = client.post(
        "/api/ai/transform-cv",
        data={
            "canonical_resume_json": json.dumps(canonical_resume),
            "jd_text": sample_jd
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "enhanced_canonical" in data
    assert "enhanced_text" in data
    assert data["total_upgrades_made"] >= 1
    # Check transformed bullet in enhanced canonical
    enhanced_bullets = data["enhanced_canonical"]["experience"][0]["bullets"]
    assert "worked on" not in enhanced_bullets[0].lower()


def test_generate_pdf_endpoint():
    """Test POST /api/ai/generate-pdf endpoint."""
    canonical_resume = {
        "candidate_name": "Swapnil Supe",
        "email": "swapnil@example.com",
        "skills": ["Python", "FastAPI", "Docker"]
    }
    res = client.post(
        "/api/ai/generate-pdf",
        data={"canonical_resume_json": json.dumps(canonical_resume)}
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert "Swapnil_Supe_ATS_Enhanced_Resume.pdf" in res.headers["content-disposition"]
    assert len(res.content) > 500


def test_compare_scores_endpoint():
    """Test POST /api/ai/compare-scores endpoint."""
    orig_text = "Python developer. worked on apps."
    enh_text = "Python developer with experience in FastAPI and Docker. Architected high-performance applications."
    jd_text = "Python Developer with FastAPI and Docker skills."

    res = client.post(
        "/api/ai/compare-scores",
        data={
            "original_text": orig_text,
            "enhanced_text": enh_text,
            "jd_text": jd_text
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "before" in data
    assert "after" in data
    assert "deltas" in data
    assert data["after"]["overall_score"] >= data["before"]["overall_score"]
    assert data["deltas"]["score_jump"] >= 0
