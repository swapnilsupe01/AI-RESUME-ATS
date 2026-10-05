"""
Regression tests for project rendering in AI Resume ATS.

Required format (Section F):
  ### **ISO Audit AI — AI-Powered ISO Audit Gap Analysis Platform**
  *React, Vite, FastAPI, Python, Gemini API, RAG, ChromaDB, Sentence Transformers, Docker, Nginx*
  - Bullet 1
  - Bullet 2

Rules tested:
  G1: subtitle appears exactly once (in the heading), never in the italic tech line
  G2: technology stack on its own italic line, not in the heading
  G3: all four named projects have subtitle AND tech line
  G4: no project receives another project's data
  G5: project with no technologies has no italic line
  G6: project with no subtitle has heading-only (just the name)
  G7: round-trip through parser preserves all fields
"""
import re
import sys
sys.path.insert(0, ".")

from app.models.canonical_resume import CanonicalResume, ProjectItem, Profile
from app.parser.markdown_pipeline import canonical_to_markdown, markdown_to_canonical


# ─────────────────────────────────────────────────────────────────────────────
# Reference projects (Section G: exact projects to test)
# ─────────────────────────────────────────────────────────────────────────────

REF_PROJECTS = [
    {
        "name": "ISO Audit AI",
        "subtitle": "AI-Powered ISO Audit Gap Analysis Platform",
        "technologies": ["React", "Vite", "FastAPI", "Python", "Gemini API", "RAG", "ChromaDB", "Sentence Transformers", "Docker", "Nginx"],
        "highlights": [
            "Built an AI-powered platform for ISO audit gap analysis using RAG and the Google Gemini API.",
            "Implemented semantic document retrieval using ChromaDB and Sentence Transformers.",
            "Developed FastAPI REST APIs and automated PDF/Excel audit report generation. Containerized using Docker Compose and Nginx.",
        ],
    },
    {
        "name": "NodeNarrate",
        "subtitle": "AI LangGraph Visual Debugger",
        "technologies": ["Python", "LangGraph", "React", "Docker", "Hugging Face"],
        "highlights": [
            "Developed an open-source visual debugging and execution-tracing tool for LangGraph agents.",
            "Built a Python SDK with callback tracing, HTML/JSON trace export, and an interactive React visualization studio.",
            "Deployed the application using Docker on Hugging Face Spaces.",
        ],
    },
    {
        "name": "JuiceScanner AI",
        "subtitle": "AI-Powered Vulnerability Scanner for OWASP Juice Shop",
        "technologies": ["React", "FastAPI", "Python", "Ollama", "Llama 3.2", "Docker", "OWASP ZAP"],
        "highlights": [
            "Built an AI-powered vulnerability scanning and intelligence platform for OWASP Juice Shop.",
            "Integrated OWASP ZAP for automated scanning; used Llama 3.2 via Ollama for AI-based vulnerability analysis.",
            "Developed a React frontend and FastAPI backend, deployed using Docker.",
        ],
    },
    {
        "name": "Resume ATS",
        "subtitle": "AI Resume Intelligence and Evidence Platform",
        "technologies": ["Python", "FastAPI", "React", "Docker", "Sentence-BERT", "Ollama"],
        "highlights": [
            "Engineered a full-stack AI-powered resume parsing, scoring, and upgrade platform.",
            "Built Layer E upgrade engine with hallucination guarding and evidence-based suggestion generation.",
            "Deployed using Docker with FastAPI backend and HTML/JS frontend.",
        ],
    },
]


def build_resume(projects_dicts, extra_projects=None):
    r = CanonicalResume()
    r.profile = Profile(name="Test Candidate")
    items = []
    for d in (projects_dicts + (extra_projects or [])):
        items.append(ProjectItem(
            name=d["name"],
            subtitle=d.get("subtitle", ""),
            description=d.get("subtitle", ""),
            highlights=d.get("highlights", []),
            technologies=d.get("technologies", []),
        ))
    r.projects = items
    return r


def parse_md_projects(md: str):
    """Return dict of {name: {heading_line, tech_line, bullets, all_lines_after_heading}}."""
    lines = md.split("\n")
    result = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            heading = line[4:].strip()
            # Extract project name from **Name — Subtitle**
            clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', heading).strip()
            name = re.split(r'\s*(?:—|–)\s*', clean)[0].strip()
            tech_line = None
            bullets = []
            j = i + 1
            while j < len(lines) and not lines[j].startswith("### ") and not lines[j].startswith("## "):
                l = lines[j].strip()
                if l.startswith("*") and l.endswith("*") and not l.startswith("**") and len(l) > 2:
                    tech_line = l[1:-1].strip()
                elif l.startswith("- "):
                    bullets.append(l[2:].strip())
                j += 1
            result[name] = {"heading": heading, "tech_line": tech_line, "bullets": bullets}
        i += 1
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TEST 1: The four reference projects — subtitle, tech, bullets all present
# ─────────────────────────────────────────────────────────────────────────────

def test_four_reference_projects():
    """G3: all four named projects have subtitle AND tech line."""
    resume = build_resume(REF_PROJECTS)
    md = canonical_to_markdown(resume)
    print("\n" + "=" * 70)
    print("TEST 1 — Four reference projects: subtitle + tech + bullets")
    print("=" * 70)
    print(md[md.find("## Key Projects"):])

    projects = parse_md_projects(md)
    errors = []

    for ref in REF_PROJECTS:
        name = ref["name"]
        if name not in projects:
            errors.append(f"Project '{name}' not found in output")
            continue
        p = projects[name]
        heading = p["heading"]
        clean_h = re.sub(r'\*\*([^*]+)\*\*', r'\1', heading)

        # G1: subtitle must be in heading (once)
        if ref["subtitle"] not in clean_h:
            errors.append(f"'{name}': subtitle missing from heading. heading='{heading[:80]}'")
        else:
            count = clean_h.count(ref["subtitle"])
            if count > 1:
                errors.append(f"'{name}': subtitle repeated {count}x in heading")
            else:
                print(f"  ✓ '{name}': subtitle in heading (×1)")

        # G2: tech line must be present and not in heading
        if p["tech_line"] is None:
            errors.append(f"'{name}': tech line is MISSING (expected italic tech line below heading)")
        else:
            # Check at least some techs are in the tech line
            missing_techs = [t for t in ref["technologies"] if t not in p["tech_line"]]
            if missing_techs:
                errors.append(f"'{name}': tech line is present but missing: {missing_techs}. tech_line='{p['tech_line'][:80]}'")
            else:
                print(f"  ✓ '{name}': all {len(ref['technologies'])} technologies on italic line")

        # Subtitle should NOT appear in the tech line
        if p["tech_line"] and ref["subtitle"].lower() in p["tech_line"].lower():
            errors.append(f"'{name}': subtitle is duplicated inside the tech line: '{p['tech_line'][:80]}'")

        # Bullets present
        if not p["bullets"]:
            errors.append(f"'{name}': no bullet points found")
        else:
            print(f"  ✓ '{name}': {len(p['bullets'])} bullet(s)")

    assert not errors, f"TEST 1 FAILED:\n" + "\n".join(f"  ✗ {e}" for e in errors)
    print("TEST 1 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 2: No duplicate subtitle (G1)
# ─────────────────────────────────────────────────────────────────────────────

def test_no_duplicate_subtitle():
    """G1: subtitle appears exactly once — in the heading only."""
    resume = build_resume(REF_PROJECTS)
    md = canonical_to_markdown(resume)
    print("\n" + "=" * 70)
    print("TEST 2 — No duplicate subtitle")
    print("=" * 70)

    errors = []
    for ref in REF_PROJECTS:
        count = md.count(ref["subtitle"])
        if count == 0:
            errors.append(f"'{ref['name']}': subtitle not found at all")
        elif count > 1:
            # Find all occurrences to diagnose
            positions = [i for i in range(len(md)) if md[i:i+len(ref["subtitle"])] == ref["subtitle"]]
            errors.append(f"'{ref['name']}': subtitle appears {count}x (positions: {positions[:5]})")
        else:
            print(f"  ✓ '{ref['name']}': subtitle appears exactly once")

    assert not errors, "TEST 2 FAILED:\n" + "\n".join(f"  ✗ {e}" for e in errors)
    print("TEST 2 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 3: Project with no subtitle
# ─────────────────────────────────────────────────────────────────────────────

def test_project_no_subtitle():
    """Project with no subtitle: heading is just the name, no em-dash."""
    resume = build_resume([{
        "name": "Demo Project",
        "subtitle": "",
        "technologies": ["Python", "Flask"],
        "highlights": ["Built a demo API."],
    }])
    md = canonical_to_markdown(resume)
    print("\n" + "=" * 70)
    print("TEST 3 — Project with no subtitle")
    print("=" * 70)
    print(md[md.find("## Key Projects"):])

    projects = parse_md_projects(md)
    assert "Demo Project" in projects, "Demo Project not found"
    p = projects["Demo Project"]
    heading_clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', p["heading"]).strip()

    assert " — " not in heading_clean, f"Em-dash found in no-subtitle heading: '{p['heading']}'"
    assert p["tech_line"] is not None, "Tech line missing for project with technologies"
    assert "Python" in p["tech_line"], f"Python not in tech line: '{p['tech_line']}'"
    assert p["bullets"], "No bullets found"
    print(f"  ✓ No em-dash in heading: '{p['heading']}'")
    print(f"  ✓ Tech line: '{p['tech_line']}'")
    print("TEST 3 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 4: Project with no technologies
# ─────────────────────────────────────────────────────────────────────────────

def test_project_no_technologies():
    """Project with no technologies: no italic tech line emitted."""
    resume = build_resume([{
        "name": "Open Source Contrib",
        "subtitle": "A collection of contributions",
        "technologies": [],
        "highlights": ["Contributed to multiple open-source Python projects."],
    }])
    md = canonical_to_markdown(resume)
    print("\n" + "=" * 70)
    print("TEST 4 — Project with no technologies")
    print("=" * 70)
    print(md[md.find("## Key Projects"):])

    projects = parse_md_projects(md)
    assert "Open Source Contrib" in projects, "Project not found"
    p = projects["Open Source Contrib"]
    assert p["tech_line"] is None, f"Tech line should be absent, got: '{p['tech_line']}'"
    assert p["bullets"], "No bullets found"
    print(f"  ✓ No tech line emitted")
    print(f"  ✓ Heading: '{p['heading']}'")
    print("TEST 4 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 5: Long technology list wraps correctly (no truncation)
# ─────────────────────────────────────────────────────────────────────────────

def test_long_technology_list():
    """Long tech lists must not be truncated — all items in the tech line."""
    long_techs = ["Python", "FastAPI", "React", "TypeScript", "Docker", "Nginx",
                  "PostgreSQL", "Redis", "Celery", "LangChain", "OpenAI API", "Pinecone"]
    resume = build_resume([{
        "name": "Full Stack AI App",
        "subtitle": "End-to-End AI Development Platform",
        "technologies": long_techs,
        "highlights": ["Built a comprehensive full-stack AI platform.", "Deployed to production on AWS."],
    }])
    md = canonical_to_markdown(resume)
    print("\n" + "=" * 70)
    print("TEST 5 — Long technology list")
    print("=" * 70)
    print(md[md.find("## Key Projects"):])

    projects = parse_md_projects(md)
    assert "Full Stack AI App" in projects, "Project not found"
    p = projects["Full Stack AI App"]
    assert p["tech_line"] is not None, "Tech line missing"
    missing = [t for t in long_techs if t not in p["tech_line"]]
    assert not missing, f"Some techs missing from tech line: {missing}"
    print(f"  ✓ All {len(long_techs)} technologies in tech line")
    print("TEST 5 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 6: Two candidates do not contaminate each other (G4)
# ─────────────────────────────────────────────────────────────────────────────

def test_no_cross_contamination():
    """G4: two different candidates' resumes have completely independent content."""
    resume_a = build_resume([REF_PROJECTS[0], REF_PROJECTS[1]])  # Alice
    resume_b = build_resume([{
        "name": "Indexify",
        "subtitle": "Personal Repository Manager",
        "technologies": ["React.js", "Node.js", "Express.js", "MySQL"],
        "highlights": ["Built a full-stack repo manager.", "Implemented JWT authentication."],
    }])

    md_a = canonical_to_markdown(resume_a)
    md_b = canonical_to_markdown(resume_b)

    # Alice should have ISO Audit AI and NodeNarrate, NOT Indexify
    assert "ISO Audit AI" in md_a, "Alice missing ISO Audit AI"
    assert "NodeNarrate" in md_a, "Alice missing NodeNarrate"
    assert "Indexify" not in md_a, "Alice has Bob's Indexify project!"

    # Bob should have Indexify, NOT ISO Audit AI
    assert "Indexify" in md_b, "Bob missing Indexify"
    assert "ISO Audit AI" not in md_b, "Bob has Alice's ISO Audit AI project!"
    assert "React" not in md_b or "React.js" in md_b, "Tech contamination check"

    print("\n  ✓ No cross-contamination between candidates")
    print("TEST 6 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 7: Round-trip — parse back preserves all fields (G7)
# ─────────────────────────────────────────────────────────────────────────────

def test_round_trip():
    """G7: parse the generated markdown back; all fields must survive."""
    resume = build_resume(REF_PROJECTS)
    md = canonical_to_markdown(resume)

    print("\n" + "=" * 70)
    print("TEST 7 — Round-trip: canonical → markdown → canonical")
    print("=" * 70)
    print("Generated markdown (projects section):")
    print(md[md.find("## Key Projects"):])

    resume2 = markdown_to_canonical(md)
    errors = []

    for ref in REF_PROJECTS:
        proj = next((p for p in resume2.projects if ref["name"].lower() in p.name.lower()), None)
        if proj is None:
            errors.append(f"'{ref['name']}' not found after round-trip parse")
            continue
        print(f"\n  Parsed '{proj.name}':")
        print(f"    subtitle    = '{proj.subtitle}'")
        print(f"    technologies = {proj.technologies}")
        print(f"    highlights  = {len(proj.highlights)} bullets")

        # Subtitle preserved
        if ref["subtitle"] and proj.subtitle.lower() != ref["subtitle"].lower():
            errors.append(f"'{ref['name']}': subtitle changed from '{ref['subtitle']}' to '{proj.subtitle}'")
        else:
            print(f"    ✓ subtitle preserved")

        # Technologies preserved
        missing_t = [t for t in ref["technologies"] if t not in proj.technologies]
        if missing_t:
            errors.append(f"'{ref['name']}': technologies lost after round-trip: {missing_t}")
        else:
            print(f"    ✓ all {len(ref['technologies'])} technologies preserved")

        # Bullets preserved
        if len(proj.highlights) < len(ref["highlights"]):
            errors.append(f"'{ref['name']}': lost bullets: expected {len(ref['highlights'])}, got {len(proj.highlights)}")
        else:
            print(f"    ✓ all {len(ref['highlights'])} bullets preserved")

    assert not errors, "TEST 7 FAILED:\n" + "\n".join(f"  ✗ {e}" for e in errors)
    print("\nTEST 7 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# TEST 8: upgrade_routes fallback renderer
# ─────────────────────────────────────────────────────────────────────────────

def test_upgrade_routes_fallback():
    """The _canonical_dict_to_markdown fallback renderer must use the same format."""
    from app.api.upgrade_routes import _canonical_dict_to_markdown

    d = {
        "profile": {"name": "Test Candidate"},
        "projects": [
            {
                "name": ref["name"],
                "subtitle": ref["subtitle"],
                "description": ref["subtitle"],
                "highlights": ref["highlights"],
                "technologies": ref["technologies"],
            }
            for ref in REF_PROJECTS
        ]
    }
    md = _canonical_dict_to_markdown(d)
    print("\n" + "=" * 70)
    print("TEST 8 — upgrade_routes fallback renderer")
    print("=" * 70)
    print(md[md.find("## Key Projects"):])

    projects = parse_md_projects(md)
    errors = []
    for ref in REF_PROJECTS:
        name = ref["name"]
        if name not in projects:
            errors.append(f"'{name}' not found in fallback renderer output")
            continue
        p = projects[name]
        if p["tech_line"] is None:
            errors.append(f"'{name}': tech line missing in fallback renderer")
        else:
            missing = [t for t in ref["technologies"][:3] if t not in p["tech_line"]]
            if missing:
                errors.append(f"'{name}': missing techs in fallback: {missing}")
            else:
                print(f"  ✓ '{name}': tech line present")
        # Subtitle not duplicated
        count = md.count(ref["subtitle"])
        if count > 1:
            errors.append(f"'{name}': subtitle duplicated {count}x in fallback output")
        else:
            print(f"  ✓ '{name}': subtitle appears exactly once")

    assert not errors, "TEST 8 FAILED:\n" + "\n".join(f"  ✗ {e}" for e in errors)
    print("TEST 8 PASSED")


# ─────────────────────────────────────────────────────────────────────────────
# Run all
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_four_reference_projects()
    test_no_duplicate_subtitle()
    test_project_no_subtitle()
    test_project_no_technologies()
    test_long_technology_list()
    test_no_cross_contamination()
    test_round_trip()
    test_upgrade_routes_fallback()
    print("\n" + "=" * 70)
    print("[ALL 8 TESTS PASSED]")
