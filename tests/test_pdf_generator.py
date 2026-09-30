"""
Unit tests for ATS PDF generator.
Run: pytest tests/test_pdf_generator.py
"""

import pytest
import pymupdf
try:
    from app.parser.pdf_generator import pdf_generator, generate_pdf
    from app.models.canonical_resume import (
        CanonicalResume,
        Profile,
        ExperienceItem,
        ProjectItem,
        EducationItem,
        CategorizedSkills,
    )
except ImportError:
    from backend.app.parser.pdf_generator import pdf_generator, generate_pdf
    from backend.app.models.canonical_resume import (
        CanonicalResume,
        Profile,
        ExperienceItem,
        ProjectItem,
        EducationItem,
        CategorizedSkills,
    )


def test_pdf_generator_basic():
    resume = CanonicalResume(
        profile=Profile(
            name="Alice Smith",
            email="alice@example.com",
            phone="+1-555-0100",
            github="https://github.com/alicesmith",
            linkedin="https://linkedin.com/in/alicesmith",
        ),
        summary="Skilled Cloud Engineer specialized in Kubernetes, Terraform, and AWS.",
        experience=[
            ExperienceItem(
                company="TechCorp",
                role="DevOps Engineer",
                location="Austin, TX",
                start_date="2022",
                end_date="Present",
                highlights=[
                    "Implemented zero-downtime deployment pipelines using ArgoCD and Helm.",
                    "Automated multi-region infrastructure provisioning using Terraform.",
                ],
            )
        ],
        projects=[
            ProjectItem(
                name="InfraOps",
                technologies=["Terraform", "Kubernetes", "AWS"],
                highlights=["Open-source infrastructure deployment automation toolkit."],
            )
        ],
        skills=CategorizedSkills(
            cloud=["AWS", "GCP", "Kubernetes", "Docker", "Terraform"],
            frameworks=["FastAPI"],
            technical=["Python", "Bash", "Go"],
        ),
        education=[
            EducationItem(
                institution="UT Austin",
                degree="B.S. in Electrical and Computer Engineering",
                graduation_year="2022",
            )
        ],
    )

    pdf_bytes = generate_pdf(resume.model_dump())
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) >= 1

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    assert "ALICE SMITH" in full_text
    assert "PROFILE" in full_text
    assert "TECHNICAL SKILLS" in full_text
    assert "EXPERIENCE" in full_text
    assert "PROJECTS" in full_text
    assert "EDUCATION" in full_text
    assert "TechCorp" in full_text
    assert "ArgoCD and Helm" in full_text
    assert "UT Austin" in full_text


def test_pdf_generator_fallback_empty():
    pdf_bytes = generate_pdf({})
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0


def test_pdf_generator_flat_dict():
    flat_data = {
        "candidate_name": "Bob Jones",
        "email": "bob@example.com",
        "summary": "Full Stack Developer",
        "extracted_skills": ["JavaScript", "React", "Node.js"],
    }
    pdf_bytes = generate_pdf(flat_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "".join(p.get_text() for p in doc)
    assert "BOB JONES" in full_text
    assert "bob@example.com" in full_text
    assert "Full Stack Developer" in full_text


def test_pdf_generator_multipage_no_is_pdf_error():
    """Ensure multi-page resumes do not raise 'NoneType' object has no attribute 'is_pdf'."""
    long_resume = {
        "profile": {"name": "Multi Page Candidate", "email": "multipage@example.com"},
        "summary": "Experienced software architect with extensive enterprise experience. " * 10,
        "experience": [
            {
                "role": f"Staff Software Engineer {i}",
                "company": f"Tech Enterprise {i}",
                "highlights": [
                    f"Architected distributed real-time microservices handling millions of events {j}"
                    for j in range(6)
                ],
            }
            for i in range(8)
        ],
        "projects": [
            {
                "name": f"Enterprise Project {i}",
                "description": "High throughput data processing framework deployed on Kubernetes.",
                "highlights": [f"Highlight bullet {k}" for k in range(3)],
            }
            for i in range(4)
        ],
        "education": [
            {
                "institution": "University of Technology",
                "degree": "M.S. in Computer Science",
                "graduation_year": "2018",
            }
        ],
    }

    pdf_bytes = generate_pdf(long_resume)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    assert len(doc) > 1, "Should span multiple pages"
    full_text = "".join(p.get_text() for p in doc)
    assert "MULTI PAGE CANDIDATE" in full_text
    assert "Tech Enterprise 0" in full_text
    assert "Tech Enterprise 7" in full_text


def test_pdf_generator_optional_custom_sections():
    """Verify that optional sections like certifications, achievements, hobbies, and custom sections render properly."""
    custom_resume = {
        "profile": {"name": "Arav Mahind", "email": "arav@example.com", "phone": "+91 9876543210"},
        "summary": "Full Stack Engineer specialized in Python, FastAPI, and Distributed Systems.",
        "skills": {
            "technical": ["Python", "JavaScript", "C++"],
            "frameworks": ["FastAPI", "React", "Next.js"],
            "databases": ["PostgreSQL", "Redis"],
            "cloud": ["AWS", "Docker", "Git"]
        },
        "experience": [
            {
                "role": "Software Engineering Intern",
                "company": "NextGen Labs",
                "start_date": "Jan 2024",
                "end_date": "Present",
                "highlights": ["Built distributed caching microservice reducing latency by 40%."]
            }
        ],
        "projects": [
            {
                "name": "AI Resume ATS",
                "highlights": ["Engineered ATS resume scoring and evidence verification engine."]
            }
        ],
        "education": [
            {
                "institution": "Pune Institute of Computer Technology",
                "degree": "B.E. in Computer Engineering",
                "start_date": "2021",
                "end_date": "2025"
            }
        ],
        "achievements": [
            {
                "title": "1st Place Winner",
                "organization": "National Smart India Hackathon 2024",
                "description": "Led team of 6 engineers."
            }
        ],
        "certifications": [
            {
                "name": "AWS Certified Developer Associate",
                "issuer": "Amazon Web Services",
                "issue_date": "2024"
            }
        ],
        "hobbies": [
            "Open Source Contributor",
            "Competitive Chess Player",
            "Technical Blogging"
        ],
        "custom_sections": [
            {
                "title": "Languages Spoken",
                "items": ["English (Fluent)", "Hindi (Native)", "German (Basic)"]
            }
        ]
    }

    pdf_bytes = generate_pdf(custom_resume)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000

    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = "".join(p.get_text() for p in doc)

    assert "ARAV MAHIND" in full_text
    assert "CERTIFICATIONS" in full_text
    assert "AWS Certified Developer Associate" in full_text
    assert "ACHIEVEMENTS" in full_text
    assert "1st Place Winner" in full_text
    assert "HOBBIES" in full_text
    assert "Competitive Chess Player" in full_text
    assert "LANGUAGES SPOKEN" in full_text
    assert "English (Fluent)" in full_text

