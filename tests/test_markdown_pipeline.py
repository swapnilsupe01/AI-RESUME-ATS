"""
Unit tests for the PDF -> Markdown -> Canonical Resume JSON Pipeline.
"""
import pytest
from app.models.canonical_resume import CanonicalResume
from app.parser.canonical_parser import get_synthetic_sample_resume, parse_text_to_canonical
from app.parser.markdown_pipeline import (
    canonical_to_markdown, markdown_to_canonical, blocks_to_markdown
)


def test_canonical_to_markdown_formatting():
    sample = get_synthetic_sample_resume()
    md = canonical_to_markdown(sample)

    assert "# Alex Chen" in md
    assert "Staff Machine Learning & Full-Stack Systems Engineer" in md
    assert "Email: alex.chen.dev@example.com" in md
    assert "## Technical Skills" in md
    assert "## Work Experience" in md
    assert "### Senior ML Infrastructure Engineer — Nexus AI Systems (Jan 2022 – Present)" in md
    assert "## Key Projects" in md
    assert "## Education" in md
    assert "## Certifications" in md


def test_markdown_to_canonical_parsing():
    sample_md = """# Taylor Swift
**Principal AI Architect**
Email: taylor.swift@example.com | Phone: 415-555-0199 | Location: New York, NY
[GitHub](https://github.com/taylorswift/ml-core) | [LinkedIn](https://linkedin.com/in/taylorswift)

## Professional Summary
Experienced software architect specializing in scalable ML and cloud infrastructure.

## Technical Skills
- **Languages & Core:** Python, Go, Rust
- **Frameworks:** FastAPI, PyTorch, React
- **Cloud & DevOps:** AWS, Docker, Kubernetes

## Work Experience
### Principal Architect — BigTech Corp (2021 – Present)
- Designed real-time event streaming pipeline processing 10B events daily.
- Decreased end-to-end data latency by 50% using Apache Kafka and Go workers.
*Technologies: Python, Go, Kafka, Docker*

## Key Projects
### VectorSearch AI ([Code](https://github.com/taylorswift/vector-search))
High performance vector search library.
- Implemented HNSW indexing in Rust with sub-5ms query latency.
*Technologies: Rust, Python*

## Education
### B.S. in Computer Science — MIT (2015 – 2019)
GPA: 3.95
"""
    resume = markdown_to_canonical(sample_md)

    assert resume.profile.name == "Taylor Swift"
    assert resume.profile.email == "taylor.swift@example.com"
    assert resume.profile.phone == "415-555-0199"
    assert resume.profile.github == "https://github.com/taylorswift/ml-core"
    assert "Experienced software architect" in resume.summary

    assert len(resume.experience) == 1
    assert resume.experience[0].role == "Principal Architect"
    assert resume.experience[0].company == "BigTech Corp"
    assert len(resume.experience[0].highlights) == 2
    assert "Kafka" in resume.experience[0].highlights[1] or "Kafka" in resume.experience[0].technologies

    assert len(resume.projects) == 1
    assert resume.projects[0].name == "VectorSearch AI"
    assert resume.projects[0].github_url == "https://github.com/taylorswift/vector-search"

    assert len(resume.education) == 1
    assert resume.education[0].institution == "MIT"
    assert resume.education[0].gpa == "3.95"


def test_empty_and_malformed_markdown():
    # Empty string
    empty_resume, md, warnings = parse_text_to_canonical("")
    assert empty_resume.profile.name == ""
    assert len(warnings) > 0

    # Minimal unformatted text
    raw = "Just some text without any sections or structure"
    res, md, warnings = parse_text_to_canonical(raw)
    assert len(res.experience) == 0
    assert len(res.skills.technical) == 0


def test_blocks_to_markdown():
    # PyMuPDF block format: (x0, y0, x1, y1, text, block_no, block_type)
    blocks = [
        (50.0, 50.0, 300.0, 70.0, "JANE DOE\nSoftware Engineer\n", 0, 0),
        (50.0, 100.0, 300.0, 120.0, "SKILLS\n", 1, 0),
        (50.0, 130.0, 300.0, 160.0, "• Python\n• FastAPI\n• Docker\n", 2, 0),
        (50.0, 200.0, 300.0, 220.0, "EXPERIENCE\n", 3, 0),
        (50.0, 230.0, 300.0, 260.0, "Lead Developer at Acme (2020 - Present)\n- Built cloud API\n", 4, 0),
    ]

    md = blocks_to_markdown(blocks)
    assert "# Jane Doe" in md
    assert "## Skills" in md
    assert "- Python" in md
    assert "## Experience" in md
