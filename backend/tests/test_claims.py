"""
Claims Quality Test Suite: Word Length & Bullet Purity Audit.

Asserts that for each fixture (resume_A.txt, resume_B.txt):
- No extracted claim exceeds 25 words.
- No claim text contains more than one bullet marker (e.g. '•', '–', '—', '*', '▪').
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest

from app.parser.resume_parser import parse_resume
from app.extraction.project_extractor import extract_projects
from app.extraction.claim_extractor import extract_all_resume_claims

POSSIBLE_DIRS = [
    Path(__file__).resolve().parent / "fixtures",
    Path(__file__).resolve().parents[2] / "tests" / "fixtures",
    Path("tests/fixtures"),
    Path("backend/tests/fixtures"),
]
FIXTURES_DIR = next((d for d in POSSIBLE_DIRS if d.exists()), None)

BULLET_MARKERS = ["•", "–", "—", "*", "▪", "►", "·"]


def load_fixture(filename: str) -> str:
    if not FIXTURES_DIR:
        raise FileNotFoundError("Could not locate fixtures directory.")
    path = FIXTURES_DIR / filename
    return path.read_text(encoding="utf-8")


def count_bullet_markers(text: str) -> int:
    return sum(text.count(marker) for marker in BULLET_MARKERS)


@pytest.mark.parametrize("fixture_name", ["resume_A.txt", "resume_B.txt"])
def test_claims_word_limit_and_bullet_marker_purity(fixture_name):
    """
    Assert that for each synthetic resume fixture:
    1. No extracted claim exceeds 25 words in length.
    2. No extracted claim contains more than one bullet marker.
    """
    resume_text = load_fixture(fixture_name)
    parsed = parse_resume(resume_text)
    projects_section = parsed.get("sections", {}).get("projects", "")

    projects = extract_projects(resume_text, projects_section)
    assert len(projects) > 0, f"Expected projects to be extracted from {fixture_name}, found none."

    for p in projects:
        p_title = p.get("title", "")
        assert "http" not in p_title.lower(), f"Project title contains 'http': {p_title}"
        assert "(github" not in p_title.lower(), f"Project title contains '(GitHub': {p_title}"

    all_project_claims = extract_all_resume_claims(projects)
    assert len(all_project_claims) > 0, f"Expected claim sets for {fixture_name}, found none."

    all_claims = []
    for proj_data in all_project_claims:
        proj_title = proj_data.get("project_title", "Unknown")
        for claim in proj_data.get("claims", []):
            claim_text = claim.get("claim", "").strip()
            claim_type = claim.get("claim_type", "")
            all_claims.append((proj_title, claim_type, claim_text))

    assert len(all_claims) > 0, f"No discrete claims extracted from {fixture_name}."

    word_limit_violations = []
    bullet_marker_violations = []

    for proj_title, claim_type, claim_text in all_claims:
        # Check 1: No claim exceeds 25 words
        words = claim_text.split()
        if len(words) > 25:
            word_limit_violations.append(
                f"[{proj_title} | {claim_type}] Word count {len(words)} > 25: '{claim_text}'"
            )

        # Check 2: No claim text contains more than one bullet marker
        marker_count = count_bullet_markers(claim_text)
        if marker_count > 1:
            bullet_marker_violations.append(
                f"[{proj_title} | {claim_type}] Multiple bullet markers ({marker_count}): '{claim_text}'"
            )

    failure_details = []
    if word_limit_violations:
        failure_details.append(
            f"Found {len(word_limit_violations)} claims exceeding 25 words:\n  "
            + "\n  ".join(word_limit_violations)
        )
    if bullet_marker_violations:
        failure_details.append(
            f"Found {len(bullet_marker_violations)} claims containing multiple bullet markers:\n  "
            + "\n  ".join(bullet_marker_violations)
        )

    assert not failure_details, (
        f"Claim extraction quality failures in {fixture_name}:\n" + "\n\n".join(failure_details)
    )
