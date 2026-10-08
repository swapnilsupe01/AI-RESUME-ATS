"""
Upgrade Structure Test Suite: Section Headings Fidelity & Skill Leakage Audit.

Asserts:
1. The generated PDF contains the same section headings as the canonical resume
   (and contains no extra headings for empty/missing sections).
2. The generated PDF contains no technical skill or tool absent from the source resume.
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import pymupdf as fitz

from app.parser.canonical_parser import parse_text_to_canonical
from app.parser.pdf_generator import pdf_generator
from app.utils.skills import extract_skills

POSSIBLE_DIRS = [
    Path(__file__).resolve().parent / "fixtures",
    Path(__file__).resolve().parents[2] / "tests" / "fixtures",
    Path("tests/fixtures"),
    Path("backend/tests/fixtures"),
]
FIXTURES_DIR = next((d for d in POSSIBLE_DIRS if d.exists()), None)


def load_fixture(filename: str) -> str:
    if not FIXTURES_DIR:
        raise FileNotFoundError("Could not locate fixtures directory.")
    path = FIXTURES_DIR / filename
    return path.read_text(encoding="utf-8")


# Standard mapping between canonical resume sections and expected PDF section heading titles
SECTION_HEADING_MAP = {
    "summary": ["PROFESSIONAL SUMMARY", "SUMMARY"],
    "skills": ["TECHNICAL SKILLS", "SKILLS"],
    "experience": ["EXPERIENCE", "WORK EXPERIENCE"],
    "projects": ["PROJECTS", "KEY PROJECTS"],
    "education": ["EDUCATION"],
    "certifications": ["CERTIFICATIONS"],
    "achievements": ["ACHIEVEMENTS"],
}


def get_canonical_active_sections(canonical) -> set:
    """Identify which sections are populated in the CanonicalResume object."""
    active = set()
    if canonical.summary and canonical.summary.strip():
        active.add("summary")

    skills = canonical.skills
    has_skills = any([
        skills.technical, skills.frameworks, skills.cloud,
        skills.databases, skills.tools, skills.cybersecurity,
        skills.soft, skills.other
    ])
    if has_skills:
        active.add("skills")

    if canonical.experience and len(canonical.experience) > 0:
        active.add("experience")

    if canonical.projects and len(canonical.projects) > 0:
        active.add("projects")

    if canonical.education and len(canonical.education) > 0:
        active.add("education")

    if canonical.certifications and len(canonical.certifications) > 0:
        active.add("certifications")

    if canonical.achievements and len(canonical.achievements) > 0:
        active.add("achievements")

    return active


@pytest.mark.parametrize("fixture_name", ["resume_A.txt", "resume_B.txt"])
def test_generated_pdf_section_headings_fidelity(fixture_name):
    """
    Assert that the generated PDF contains exactly the section headings present
    in the canonical resume, and does not render headings for absent sections.
    """
    resume_text = load_fixture(fixture_name)
    canonical, _, _ = parse_text_to_canonical(resume_text)

    # Render PDF from canonical resume data
    canonical_dict = canonical.model_dump()
    pdf_bytes = pdf_generator.generate_pdf(canonical_dict)
    assert len(pdf_bytes) > 500, "PDF generation produced empty or invalid byte stream"

    # Extract all text from rendered PDF
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_text = "\n".join(page.get_text() for page in pdf_doc)
    pdf_doc.close()
    pdf_text_upper = pdf_text.upper()

    active_sections = get_canonical_active_sections(canonical)

    # 1. Assert all active canonical sections have corresponding headings in the PDF
    missing_headings = []
    for section in active_sections:
        possible_titles = SECTION_HEADING_MAP.get(section, [])
        if not any(title in pdf_text_upper for title in possible_titles):
            missing_headings.append(f"Section '{section}' (expected one of {possible_titles})")

    assert not missing_headings, (
        f"PDF generated from {fixture_name} is missing active section headings:\n  "
        + "\n  ".join(missing_headings)
    )

    # 2. Assert sections absent from canonical resume do NOT appear as headers in the PDF
    phantom_headings = []
    all_known_sections = set(SECTION_HEADING_MAP.keys())
    inactive_sections = all_known_sections - active_sections

    for section in inactive_sections:
        possible_titles = SECTION_HEADING_MAP.get(section, [])
        # Check if the heading appears as a standalone header in the PDF
        for title in possible_titles:
            if f"\n{title}\n" in f"\n{pdf_text_upper}\n":
                phantom_headings.append(f"Section '{section}' appeared via header '{title}'")

    assert not phantom_headings, (
        f"PDF generated from {fixture_name} contains phantom headings for empty/absent sections:\n  "
        + "\n  ".join(phantom_headings)
    )


@pytest.mark.parametrize("fixture_name", ["resume_A.txt", "resume_B.txt"])
def test_generated_pdf_contains_no_absent_skills(fixture_name):
    """
    Assert that the generated PDF contains no skills or tools that were absent
    from the original source resume.
    """
    resume_text = load_fixture(fixture_name)
    canonical, _, _ = parse_text_to_canonical(resume_text)

    # Compile the comprehensive whitelist of skills/tools present in the source resume
    source_extracted_skills = {s.lower() for s in extract_skills(resume_text)}

    # Also include skills directly listed in canonical structure
    skills_obj = canonical.skills
    canonical_skills = set()
    for cat in [skills_obj.technical, skills_obj.frameworks, skills_obj.cloud,
                skills_obj.databases, skills_obj.tools, skills_obj.cybersecurity,
                skills_obj.soft, skills_obj.other]:
        canonical_skills.update(s.lower() for s in cat)

    # Also include tech from experience and projects
    for exp in canonical.experience:
        canonical_skills.update(t.lower() for t in exp.technologies)
    for proj in canonical.projects:
        canonical_skills.update(t.lower() for t in proj.technologies)

    source_skills_whitelist = source_extracted_skills.union(canonical_skills)

    # Generate PDF
    pdf_bytes = pdf_generator.generate_pdf(canonical.model_dump())
    pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pdf_text = "\n".join(page.get_text() for page in pdf_doc)
    pdf_doc.close()

    # Extract skills found in generated PDF
    pdf_extracted_skills = {s.lower() for s in extract_skills(pdf_text)}

    # Identify any skills in the PDF that were absent from the source resume
    hallucinated_or_injected_skills = pdf_extracted_skills - source_skills_whitelist

    assert not hallucinated_or_injected_skills, (
        f"PDF generated from {fixture_name} introduced skills absent from the source resume:\n"
        f"  Injected skills: {sorted(list(hallucinated_or_injected_skills))}\n"
        f"  Source skills whitelist count: {len(source_skills_whitelist)}"
    )
