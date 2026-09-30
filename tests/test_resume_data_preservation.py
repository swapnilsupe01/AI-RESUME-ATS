"""
Regression Test Suite: Resume Data Preservation & AI Leakage Prevention.

Ensures:
1. Zero data loss: All user factual entities (contact, portfolio, education entries,
   CGPA/percentage, dates, certifications, project details) are strictly preserved.
2. Zero structural corruption: Bullets with technical commas or dashes are never turned into fake job headers.
3. Zero AI commentary leakage: Meta-explanations ("Note: ...", "Here is...", etc.) are rejected/stripped.
4. Deterministic rendering: Canonical model remains the single source of truth.
"""

import pytest
import pymupdf as fitz
from app.models.canonical_resume import (
    CanonicalResume, Profile, EducationItem, ExperienceItem, ProjectItem,
    CertificationItem, CategorizedSkills
)
from app.generation.preservation_validator import (
    contains_ai_leakage, sanitize_ai_text, validate_and_preserve
)
from app.generation.suggestion_manager import UpgradeSession, Suggestion
from app.parser.markdown_pipeline import canonical_to_markdown, markdown_to_canonical
from app.parser.pdf_generator import pdf_generator


@pytest.fixture
def swapnil_canonical_resume() -> CanonicalResume:
    """Fixture providing the complete reference resume representation."""
    return CanonicalResume(
        profile=Profile(
            name="Swapnil Supe",
            email="swapnilsupe14@gmail.com",
            phone="+91 9152342504",
            location="Mumbai, India",
            github="https://github.com/swapnilsupe01",
            linkedin="https://linkedin.com/in/swapnilsupe01",
            portfolio="https://swapnilsupe.tech"
        ),
        summary="Full Stack Developer & AI Engineer specializing in distributed Python backends, FastAPI microservices, and semantic retrieval systems.",
        education=[
            EducationItem(
                institution="Vidyalankar Institute of Technology",
                degree="B.Tech",
                field_of_study="Computer Engineering",
                start_date="2024",
                end_date="2027",
                gpa="8.5 CGPA"
            ),
            EducationItem(
                institution="Bharati Vidyapeeth Institute of Technology, Kharghar",
                degree="Diploma",
                field_of_study="Computer Technology",
                start_date="2022",
                end_date="2024",
                gpa="83.83%"
            )
        ],
        experience=[
            ExperienceItem(
                role="Team Lead & Full Stack Developer Intern",
                company="MokBuzz Solution Pvt. Ltd.",
                location="Navi Mumbai, India",
                start_date="Feb 2026",
                end_date="Present",
                current=True,
                highlights=[
                    "Spearheaded core backend architecture for enterprise client workflows using FastAPI, PostgreSQL, and Celery.",
                    "Implemented asynchronous task pipelines — cutting batch document processing duration by 42%.",
                    "Mentored 4 junior engineering interns on test-driven development, Docker containerization, and Git workflows."
                ],
                technologies=["FastAPI", "Python", "PostgreSQL", "Docker", "Celery", "Redis"]
            )
        ],
        projects=[
            ProjectItem(
                name="AI-Powered ISO Audit Gap Analysis Platform",
                description="Automated enterprise ISO compliance auditing engine utilizing LLM evaluation agents.",
                highlights=[
                    "Engineered multi-agent compliance parser comparing internal standard operating procedures against ISO 27001 clauses.",
                    "Achieved 94% recall across 300+ audit verification criteria using hybrid vector and BM25 retrieval."
                ],
                technologies=["FastAPI", "Python", "LangChain", "ChromaDB", "Docker"],
                github_url="https://github.com/swapnilsupe01/iso-audit-ai"
            ),
            ProjectItem(
                name="AI-Resume-ATS",
                description="Production ATS resume diagnostics and tailoring engine with verifiable candidate profiling.",
                highlights=[
                    "Designed PyMuPDF semantic layout extractor retaining typography, font sizes, and structural hierarchies.",
                    "Built single-source canonical resume representation with strict zero-data-loss validation."
                ],
                technologies=["FastAPI", "Python", "PyMuPDF", "SentenceTransformers"],
                github_url="https://github.com/swapnilsupe01/ai-resume-ats"
            )
        ],
        certifications=[
            CertificationItem(
                name="Programming in Java",
                issuer="NPTEL",
                issue_date="2023"
            ),
            CertificationItem(
                name="Cloud Computing",
                issuer="C-DAC",
                issue_date="2024"
            )
        ],
        skills=CategorizedSkills(
            technical=["Python", "Java", "C++", "JavaScript", "TypeScript"],
            frameworks=["FastAPI", "Django", "React", "Next.js"],
            databases=["PostgreSQL", "MongoDB", "Redis"],
            cloud=["Docker", "AWS", "GitHub Actions"],
            tools=["Git", "Postman", "Linux", "Pytest"]
        )
    )


# ---------------------------------------------------------------------------
# 1. AI Leakage Detection & Sanitization Tests
# ---------------------------------------------------------------------------

def test_ai_leakage_detection():
    """Verify that all varieties of LLM reasoning, preambles, and meta-notes are detected."""
    leaked_samples = [
        "Note: I've updated the bullet point to highlight leadership metrics.",
        "Note: I've maintained the original institution and degree factual data.",
        "Here is the tailored version of your resume:",
        "Sure, I'd be happy to help tailor your resume. Here are the improved bullets:",
        "As an AI assistant, I have restructured your experience section.",
        "Below is the ATS-optimized resume for your review:\n\n# Swapnil Supe",
        "**Rationale:** Changed passive verbs to active verbs for ATS scoring.",
        "Improvements made:\n- Added STAR metrics\n- Injected keywords"
    ]
    for sample in leaked_samples:
        assert contains_ai_leakage(sample), f"Failed to detect leakage in: {sample}"

    clean_samples = [
        "Spearheaded core backend architecture for enterprise client workflows using FastAPI.",
        "Vidyalankar Institute of Technology",
        "Full Stack Developer & AI Engineer specializing in distributed systems.",
        "Programming in Java — NPTEL (2023)"
    ]
    for clean in clean_samples:
        assert not contains_ai_leakage(clean), f"False positive leakage detected in: {clean}"


def test_sanitize_ai_text():
    """Verify that sanitize_ai_text completely removes meta-commentary from text blocks."""
    dirty_text = (
        "Here is the optimized bullet point:\n"
        "Architected high-throughput REST APIs using FastAPI, decreasing latency by 35%.\n"
        "Note: I've maintained all your original technologies."
    )
    cleaned = sanitize_ai_text(dirty_text)
    assert "Here is the" not in cleaned
    assert "Note: I've" not in cleaned
    assert "Architected high-throughput REST APIs" in cleaned


# ---------------------------------------------------------------------------
# 2. Deep Validation & Auto-Restoration (validate_and_preserve)
# ---------------------------------------------------------------------------

def test_validate_and_preserve_restores_dropped_education(swapnil_canonical_resume):
    """When an LLM drops an education entry (e.g. Diploma), validator must restore it."""
    orig_dict = swapnil_canonical_resume.model_dump()
    # Simulate lossy LLM output that only kept B.Tech and dropped Diploma
    lossy_dict = swapnil_canonical_resume.model_dump()
    lossy_dict["education"] = [lossy_dict["education"][0]]  # Dropped Bharati Vidyapeeth Diploma!

    restored, warnings = validate_and_preserve(orig_dict, lossy_dict)
    edu_list = restored.get("education", [])
    assert len(edu_list) == 2, "Failed to restore missing Diploma education entry!"

    institutions = [e.get("institution") for e in edu_list]
    assert any("Bharati Vidyapeeth" in inst for inst in institutions)
    assert any("Vidyalankar" in inst for inst in institutions)
    assert any("Bharati Vidyapeeth" in w for w in warnings), "No warning emitted for dropped education!"


def test_validate_and_preserve_restores_dropped_certifications(swapnil_canonical_resume):
    """When an LLM drops C-DAC or NPTEL certifications, validator must restore them."""
    orig_dict = swapnil_canonical_resume.model_dump()
    lossy_dict = swapnil_canonical_resume.model_dump()
    lossy_dict["certifications"] = []  # LLM dropped all certifications!

    restored, warnings = validate_and_preserve(orig_dict, lossy_dict)
    certs = restored.get("certifications", [])
    assert len(certs) == 2, "Failed to restore missing certifications!"
    cert_names = [c.get("name") for c in certs]
    assert "Programming in Java" in cert_names
    assert "Cloud Computing" in cert_names


def test_validate_and_preserve_preserves_portfolio_and_contacts(swapnil_canonical_resume):
    """Ensure portfolio URL and contact channels are never lost in transformation."""
    orig_dict = swapnil_canonical_resume.model_dump()
    lossy_dict = swapnil_canonical_resume.model_dump()
    lossy_dict["profile"]["portfolio"] = ""  # Lossy transformation cleared portfolio

    restored, _ = validate_and_preserve(orig_dict, lossy_dict)
    assert restored["profile"]["portfolio"] == "https://swapnilsupe.tech"
    assert restored["profile"]["email"] == "swapnilsupe14@gmail.com"
    assert restored["profile"]["github"] == "https://github.com/swapnilsupe01"


def test_validate_and_preserve_preserves_gpa_and_dates(swapnil_canonical_resume):
    """Ensure GPA/percentages and dates are preserved if LLM output strips them."""
    orig_dict = swapnil_canonical_resume.model_dump()
    lossy_dict = swapnil_canonical_resume.model_dump()
    # Strip GPA and dates from education items in lossy dict
    for edu in lossy_dict["education"]:
        edu["gpa"] = ""
        edu["start_date"] = ""

    restored, _ = validate_and_preserve(orig_dict, lossy_dict)
    for edu in restored["education"]:
        assert edu.get("gpa") != "", f"GPA was lost for {edu.get('institution')}"
        assert edu.get("start_date") != "", f"Start date was lost for {edu.get('institution')}"


# ---------------------------------------------------------------------------
# 3. UpgradeSession Failsafe Tests
# ---------------------------------------------------------------------------

def test_upgrade_session_build_approved_resume_defense(swapnil_canonical_resume):
    """Verify UpgradeSession auto-corrects lossy suggestions and strips AI notes."""
    orig_dict = swapnil_canonical_resume.model_dump()
    # UpgradeSession(canonical_resume, session_id)
    session = UpgradeSession(orig_dict, "test-session-123")

    # Suggestion with AI note commentary — args: section, item_id, field, original_text, suggested_text, explanation
    sugg = Suggestion(
        section="summary",
        item_id="",
        field="summary",
        original_text=orig_dict["summary"],
        suggested_text=(
            "Note: I have tailored this for ATS keyword alignment.\n"
            "High-impact Full Stack Developer and AI Engineer with deep expertise in Python, FastAPI microservices, and LLM systems."
        ),
        explanation="Improve keyword presence",
    )
    session.add_suggestion(sugg)
    session.accept(sugg.id)

    approved = session.build_approved_resume()
    # Verify AI commentary is completely eliminated
    assert "Note: I have tailored" not in approved["summary"]
    assert "High-impact Full Stack Developer" in approved["summary"]

    # Verify all original education and certifications are intact
    assert len(approved["education"]) == 2
    assert len(approved["certifications"]) == 2
    assert approved["profile"]["portfolio"] == "https://swapnilsupe.tech"


# ---------------------------------------------------------------------------
# 4. Markdown Pipeline Round-Trip & Sub-Header Protection
# ---------------------------------------------------------------------------

def test_markdown_pipeline_preserves_swapnil_resume(swapnil_canonical_resume):
    """Ensure canonical_to_markdown -> markdown_to_canonical round trip retains 100% of factual data."""
    md = canonical_to_markdown(swapnil_canonical_resume)

    # Verify markdown representation contains all key data points
    assert "Portfolio" in md
    assert "https://swapnilsupe.tech" in md
    assert "Vidyalankar Institute of Technology" in md
    assert "Bharati Vidyapeeth Institute of Technology, Kharghar" in md
    assert "8.5" in md
    assert "83.83%" in md
    assert "Programming in Java" in md
    assert "NPTEL" in md
    assert "Cloud Computing" in md
    assert "C-DAC" in md
    assert "AI-Powered ISO Audit Gap Analysis Platform" in md

    # Parse back to canonical
    parsed = markdown_to_canonical(md)

    assert parsed.profile.name == "Swapnil Supe"
    assert parsed.profile.portfolio == "https://swapnilsupe.tech"
    assert len(parsed.education) == 2, f"Expected 2 education items, got {len(parsed.education)}"
    
    # Institution name with comma must not be truncated
    bv_edu = next((e for e in parsed.education if "Bharati Vidyapeeth" in e.institution), None)
    assert bv_edu is not None, "Bharati Vidyapeeth education entry was lost!"
    assert "Kharghar" in bv_edu.institution, "Comma in institution name caused truncation!"
    assert "83.83%" in bv_edu.gpa, f"Percentage 83.83% lost, got: {bv_edu.gpa}"

    vit_edu = next((e for e in parsed.education if "Vidyalankar" in e.institution), None)
    assert vit_edu is not None, "Vidyalankar education entry was lost!"
    assert "8.5" in vit_edu.gpa, f"CGPA 8.5 lost, got: {vit_edu.gpa}"

    # Verify certifications
    assert len(parsed.certifications) >= 2, f"Expected >=2 certs, got {len(parsed.certifications)}"
    cdac_cert = next((c for c in parsed.certifications if "Cloud" in c.name or "C-DAC" in c.issuer or "C-DAC" in c.name), None)
    assert cdac_cert is not None, "C-DAC Cloud Computing certification was lost!"

    # Verify experience bullets were not broken into fake jobs
    assert len(parsed.experience) == 1, f"Expected exactly 1 experience entry, got {len(parsed.experience)}"
    assert parsed.experience[0].company == "MokBuzz Solution Pvt. Ltd."
    assert len(parsed.experience[0].highlights) == 3


def test_bullet_with_dash_does_not_become_fake_job():
    """Verify that a bullet point with an em-dash ('—') does not get corrupted into a new job/company header."""
    md = """# Candidate Name
Email: dev@example.com

## Work Experience
### Backend Engineer — Startup Co (2023 – Present)
- Architected asynchronous event pipeline — reducing latency by 45% across all endpoints.
- Spearheaded database indexing — optimized slow queries from 2.4s to 80ms.
- Built automated reporting pipeline with Python and PostgreSQL.
"""
    resume = markdown_to_canonical(md)
    assert len(resume.experience) == 1, f"Expected 1 job, got {len(resume.experience)} (bullets were corrupted into jobs!)"
    assert resume.experience[0].role == "Backend Engineer"
    assert resume.experience[0].company == "Startup Co"
    assert len(resume.experience[0].highlights) == 3


# ---------------------------------------------------------------------------
# 5. PDF Generator Text Output Verification
# ---------------------------------------------------------------------------

def test_pdf_generation_preserves_all_data_and_omits_ai_leakage(swapnil_canonical_resume):
    """Verify generated PDF contains all original factual entities and zero AI notes."""
    resume_dict = swapnil_canonical_resume.model_dump()
    pdf_bytes = pdf_generator.generate_pdf(resume_dict)
    assert len(pdf_bytes) > 1000

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = ""
    for page in doc:
        all_text += page.get_text() + "\n"

    # Verify contact & portfolio
    assert "SWAPNIL SUPE" in all_text.upper()
    assert "swapnilsupe14@gmail.com" in all_text
    assert "swapnilsupe.tech" in all_text

    # Verify both education institutions and scores
    assert "Vidyalankar Institute of Technology" in all_text
    assert "Bharati Vidyapeeth Institute of Technology" in all_text
    assert "8.5" in all_text
    assert "83.83%" in all_text

    # Verify certifications
    assert "Programming in Java" in all_text or "NPTEL" in all_text
    assert "Cloud Computing" in all_text or "C-DAC" in all_text

    # Verify zero AI commentary
    assert not contains_ai_leakage(all_text)
    assert "Note: I've" not in all_text
    assert "Here is the" not in all_text
