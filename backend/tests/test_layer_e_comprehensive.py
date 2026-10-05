# -*- coding: utf-8 -*-
"""
Comprehensive regression tests for Layer E fixes:
  1. Project name/subtitle/tech preservation
  2. Skills two-column layout and cybersecurity category
  3. Skills label normalization
  4. Grammar/unsupported-verb detection
  5. Accept/reject suggestion correctness
  6. No cross-candidate contamination
"""
import sys, copy
sys.path.insert(0, ".")

PASS = 0
FAIL = 0

def check(label, condition, info=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}" + (f" -- {info}" if info else ""))
        FAIL += 1

# ─────────────────────────────────────────────────────────────────────────────
# Setup: build two candidate resumes to test cross-contamination
# ─────────────────────────────────────────────────────────────────────────────
from app.models.canonical_resume import (
    CanonicalResume, ProjectItem, Profile, CategorizedSkills
)
from app.parser.markdown_pipeline import canonical_to_markdown, build_categorized_skills

def make_candidate_a():
    r = CanonicalResume()
    r.profile = Profile(name="Alice Dev")
    r.skills = CategorizedSkills(
        technical=["Python", "JavaScript", "Java", "Dart", "SQL"],
        frameworks=["React.js", "Vite", "Tailwind CSS", "FastAPI", "Node.js", "Flask",
                    "Scikit-learn", "TensorFlow", "LangChain", "Ollama", "Gemini API",
                    "Sentence Transformers"],
        databases=["Firebase", "Supabase", "ChromaDB"],
        cybersecurity=["OWASP Juice Shop", "Nuclei", "Selenium", "WhatWeb",
                       "Subfinder", "testssl.sh"],
        cloud=["Docker", "Docker Compose", "Nginx", "FastPanel", "Google Cloud"],
        tools=["Git", "GitHub", "OpenCV", "YOLOv8"],
    )
    r.projects = [
        ProjectItem(
            name="ISO Audit AI",
            description="AI-Powered ISO Audit Gap Analysis Platform",
            highlights=[
                "Built an AI-powered platform for ISO audit gap analysis using RAG and the Google Gemini API.",
                "Implemented semantic document retrieval using ChromaDB and Sentence Transformers.",
                "Developed FastAPI REST APIs, automated PDF/Excel audit report generation, and containerized the application using Docker Compose and Nginx.",
            ],
            technologies=["Python", "FastAPI", "ChromaDB", "Sentence Transformers", "Google Gemini API", "Docker", "Nginx"],
        ),
        ProjectItem(
            name="NodeNarrate",
            description="AI LangGraph Visual Debugger",
            highlights=[
                "Developed an open-source visual debugging and execution-tracing tool for LangGraph agents.",
                "Built a Python SDK with callback tracing, HTML/JSON trace export, and an interactive React visualization studio.",
            ],
            technologies=["Python", "LangGraph", "React", "Docker", "Hugging Face"],
        ),
    ]
    return r

def make_candidate_b():
    r = CanonicalResume()
    r.profile = Profile(name="Bob Engineer")
    r.skills = CategorizedSkills(
        technical=["Java", "C++"],
        frameworks=["Spring Boot"],
        cloud=["AWS", "Kubernetes"],
        tools=["Jira", "Git"],
    )
    r.projects = [
        ProjectItem(
            name="Indexify",
            description="Personal Repository Manager",
            highlights=[
                "Built a full-stack repository management platform with JWT authentication, CRUD operations, file uploads, version control, analytics, and advanced search.",
            ],
            technologies=["React.js", "Node.js", "Express.js", "MySQL"],
        ),
        ProjectItem(
            name="Aura Crime Intel",
            description="AI-Powered Crime Prediction Platform",
            highlights=[
                "Built an end-to-end AI application for crime-trend prediction using a Random Forest model and Flask REST APIs.",
            ],
            technologies=["React.js", "Flask", "Python", "Scikit-learn"],
        ),
    ]
    return r

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 1: Project subtitle preservation in markdown
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 1: Project Name/Subtitle/Tech Preservation ===")

resume_a = make_candidate_a()
md_a = canonical_to_markdown(resume_a)

# 1a. NodeNarrate should have "AI LangGraph Visual Debugger" in heading (new single-line format)
check("NodeNarrate subtitle in heading",
      "NodeNarrate" in md_a and "AI LangGraph Visual Debugger" in md_a,
      f"markdown excerpt: {md_a[md_a.find('NodeNarrate'):md_a.find('NodeNarrate')+150] if 'NodeNarrate' in md_a else 'NOT FOUND'}")

# 1b. ISO Audit AI subtitle in heading
check("ISO Audit AI subtitle in heading",
      "AI-Powered ISO Audit Gap Analysis Platform" in md_a)

# 1c. Heading should include em-dash separator for NodeNarrate
for line in md_a.split("\n"):
    if line.startswith("### ") and "NodeNarrate" in line:
        check("NodeNarrate heading contains em-dash separator (single-line format)",
              " — " in line or " – " in line,
              f"title line: {line}")
        break

# 1d. Technologies should be in heading (after pipe) or still present in output
check("NodeNarrate technologies present in output",
      "Python" in md_a and "LangGraph" in md_a)

# 1e. Bullet points present
check("ISO Audit AI has bullet points",
      "Built an AI-powered platform" in md_a)

# Candidate B
resume_b = make_candidate_b()
md_b = canonical_to_markdown(resume_b)

check("Indexify subtitle in heading (Personal Repository Manager)",
      "Personal Repository Manager" in md_b)

check("Aura Crime Intel subtitle in heading (AI-Powered Crime Prediction Platform)",
      "AI-Powered Crime Prediction Platform" in md_b)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 2: Skills categorization and label correctness
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 2: Skills Categorization & Labels ===")

from app.utils.skills import get_skill_category

# 2a. Cybersecurity tools route correctly
for tool, expected_cat in [
    ("OWASP Juice Shop", "cybersecurity"),
    ("Nuclei", "cybersecurity"),
    ("Subfinder", "cybersecurity"),
    ("testssl.sh", "cybersecurity"),
    ("Selenium", "cybersecurity"),
    ("WhatWeb", "cybersecurity"),
]:
    cat = get_skill_category(tool)
    check(f"'{tool}' categorized as cybersecurity", cat == "cybersecurity",
          f"got: {cat}")

# 2b. Normal tools still categorize correctly
for tool, expected_cat in [
    ("Python", "technical"),
    ("Docker", "cloud"),
    ("FastAPI", "frameworks"),
    ("Git", "tools"),
    ("Firebase", "databases"),
]:
    cat = get_skill_category(tool)
    check(f"'{tool}' categorized correctly (expected={expected_cat})",
          cat in (expected_cat, "other"),  # 'other' allowed if not in tree.json
          f"got: {cat}")

# 2c. CategorizedSkills has cybersecurity field
check("CategorizedSkills has cybersecurity field",
      hasattr(CategorizedSkills(), "cybersecurity"))

# 2d. build_categorized_skills routes security tools to cybersecurity
cat_skills = build_categorized_skills([
    "Python", "OWASP Juice Shop", "Nuclei", "Docker", "FastAPI",
    "Firebase", "Git", "Subfinder", "React.js"
])
check("OWASP Juice Shop in cybersecurity after build_categorized_skills",
      "OWASP Juice Shop" in cat_skills.cybersecurity,
      f"cybersecurity: {cat_skills.cybersecurity}")
check("Nuclei in cybersecurity after build_categorized_skills",
      "Nuclei" in cat_skills.cybersecurity,
      f"cybersecurity: {cat_skills.cybersecurity}")

# 2e. Markdown output uses new labels
check("Markdown uses 'Languages:' label (not 'Programming Languages:')",
      "**Languages:**" in md_a,
      "snippet: " + md_a[max(0,md_a.find("Languages")-5):md_a.find("Languages")+40] if "Languages" in md_a else "NOT FOUND")
check("Markdown uses 'Cybersecurity:' label",
      "**Cybersecurity:**" in md_a,
      "skills section: " + md_a[md_a.find("Technical Skills"):md_a.find("Technical Skills")+400] if "Technical Skills" in md_a else "SECTION NOT FOUND")
check("Markdown uses 'Cloud & DevOps:' label",
      "**Cloud & DevOps:**" in md_a)
check("Markdown uses 'Databases:' label",
      "**Databases:**" in md_a)

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 3: PDF skill rows ordering
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 3: PDF _collect_skill_rows Label Ordering ===")
from app.parser.pdf_generator import ATSPdfGenerator

gen = ATSPdfGenerator()

skills_data = {
    "technical": ["Python", "JavaScript"],
    "frameworks": ["React.js", "FastAPI", "LangChain"],
    "cloud": ["Docker", "Nginx"],
    "databases": ["ChromaDB", "Firebase"],
    "tools": ["Git", "GitHub"],
    "cybersecurity": ["Nuclei", "OWASP Juice Shop"],
    "soft": ["Communication"],
    "other": ["Agile"],
}

rows = gen._collect_skill_rows({"skills": skills_data})
labels = [r[0] for r in rows]

check("Languages row present", "Languages" in labels, f"rows: {labels}")
check("Frameworks & Libraries row present", "Frameworks & Libraries" in labels)
check("Cloud & DevOps row present", "Cloud & DevOps" in labels)
check("Databases row present", "Databases" in labels)
check("Tools row present", "Tools" in labels)
check("Cybersecurity row present", "Cybersecurity" in labels)

# Check ordering: Languages before Cybersecurity
if "Languages" in labels and "Cybersecurity" in labels:
    check("Languages comes before Cybersecurity in row order",
          labels.index("Languages") < labels.index("Cybersecurity"))

# Two-column pairing: Languages(0) pairs with Frameworks(1), Cloud(2) pairs with Databases(3)...
check("Correct number of rows (8 canonical fields)",
      len(rows) == 8,
      f"got {len(rows)} rows: {labels}")

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 4: Hallucination guard — unsupported verb detection
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 4: Grammar / Hallucination Guard ===")
from app.generation.hallucination_guard import classify_suggestion

original = "Developed FastAPI REST APIs and automated PDF/Excel audit report generation containerized with Docker, Compose and Nginx."
# Suggested adds "deployed" which is NOT in original
suggested_bad = "Developed and deployed FastAPI REST APIs, automated PDF/Excel audit report generation, and containerized the solution with Docker, Compose, and Nginx."
status, note = classify_suggestion(original, suggested_bad, ["FastAPI", "Docker", "Nginx", "Python"])
check("Suggestion adding 'deployed' flagged as needs_confirmation",
      status == "needs_confirmation",
      f"status={status}, note={note[:100]}")
check("Note mentions 'deployed' verb",
      "deployed" in note.lower(),
      f"note: {note[:120]}")

# Safe revision should be supported
suggested_safe = "Developed FastAPI REST APIs, automated PDF/Excel audit report generation, and containerized the application using Docker Compose and Nginx."
status2, note2 = classify_suggestion(original, suggested_safe, ["FastAPI", "Docker", "Nginx", "Python"])
check("Safe revision (no new verbs/tools) classified as supported",
      status2 == "supported",
      f"status={status2}, note={note2[:100]}")

# Test metric fabrication
sugg_with_metric = "Developed FastAPI REST APIs reducing latency by 40% and automated PDF/Excel audit report generation containerized with Docker and Nginx."
status3, note3 = classify_suggestion(original, sugg_with_metric, ["FastAPI", "Docker"])
check("Suggestion with fabricated metric flagged",
      status3 in ("needs_confirmation", "unsupported"),
      f"status={status3}")

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 5: Accept / Reject suggestion correctness
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 5: Accept / Reject / Custom Edit Correctness ===")
from app.generation.suggestion_manager import UpgradeSession, Suggestion, create_session, get_session

# Build a canonical resume dict for candidate A
canonical_a = {
    "candidate_name": "Alice Dev",
    "summary": "Python developer with AI focus.",
    "projects": [
        {
            "id": "proj_0",
            "name": "ISO Audit AI",
            "description": "AI-Powered ISO Audit Gap Analysis Platform",
            "highlights": [
                "Built an AI-powered platform for ISO audit gap analysis.",
                "Implemented semantic document retrieval using ChromaDB.",
                "Developed FastAPI REST APIs and automated PDF/Excel audit report generation.",
            ],
            "technologies": ["Python", "FastAPI", "ChromaDB", "Docker"],
        },
        {
            "id": "proj_1",
            "name": "NodeNarrate",
            "description": "AI LangGraph Visual Debugger",
            "highlights": [
                "Developed an open-source visual debugging tool for LangGraph agents.",
            ],
            "technologies": ["Python", "LangGraph", "React"],
        },
    ],
    "skills": {
        "technical": ["Python", "JavaScript"],
        "frameworks": ["FastAPI", "React"],
        "cloud": ["Docker"],
        "databases": ["ChromaDB"],
        "cybersecurity": [],
        "tools": ["Git"],
        "soft": [],
        "other": [],
    }
}

session_a = create_session("sess_a", copy.deepcopy(canonical_a))

# Add a suggestion for ISO Audit AI description
s1 = Suggestion(
    section="project",
    item_id="proj_0",
    field="description",
    original_text="AI-Powered ISO Audit Gap Analysis Platform",
    suggested_text="Intelligent ISO Compliance Audit Gap Analysis Platform",
    explanation="Adds 'Intelligent' and 'Compliance' for clarity.",
    jd_requirement="Project technical depth",
    evidence_status="supported",
    evidence_note="No new tools added.",
)
session_a.add_suggestion(s1)
s1_id = s1.suggestion_id

# Add a suggestion for NodeNarrate bullet
s2 = Suggestion(
    section="project",
    item_id="proj_1",
    field="highlights[0]",
    original_text="Developed an open-source visual debugging tool for LangGraph agents.",
    suggested_text="Built and open-sourced a visual debugging and execution-tracing tool for LangGraph agents.",
    explanation="Stronger action verb.",
    jd_requirement="Technical execution",
    evidence_status="supported",
    evidence_note="No new tools.",
)
session_a.add_suggestion(s2)
s2_id = s2.suggestion_id

# 5a. Accept s1 and verify it is applied to ISO Audit AI description
session_a.accept_suggestion(s1_id)
approved = session_a.build_approved_resume()

iso_proj = next((p for p in approved["projects"] if p.get("id") == "proj_0"), None)
check("Accepted suggestion applied to ISO Audit AI description",
      iso_proj and iso_proj["description"] == "Intelligent ISO Compliance Audit Gap Analysis Platform",
      f"got: {iso_proj['description'] if iso_proj else 'NOT FOUND'}")

# 5b. NodeNarrate (s2 still pending) should NOT be changed
node_proj = next((p for p in approved["projects"] if p.get("id") == "proj_1"), None)
orig_bullet = "Developed an open-source visual debugging tool for LangGraph agents."
check("Pending suggestion NOT applied (NodeNarrate bullet unchanged)",
      node_proj and node_proj["highlights"][0] == orig_bullet,
      f"got: {node_proj['highlights'][0] if node_proj else 'NOT FOUND'}")

# 5c. Reject s2 and confirm original preserved
session_a.reject_suggestion(s2_id)
approved2 = session_a.build_approved_resume()
node_proj2 = next((p for p in approved2["projects"] if p.get("id") == "proj_1"), None)
check("Rejected suggestion NOT applied (NodeNarrate bullet still original)",
      node_proj2 and node_proj2["highlights"][0] == orig_bullet,
      f"got: {node_proj2['highlights'][0] if node_proj2 else 'NOT FOUND'}")

# 5d. Custom edit override
s3 = Suggestion(
    section="summary",
    item_id="summary",
    field="summary",
    original_text="Python developer with AI focus.",
    suggested_text="Experienced Python and AI developer.",
    explanation="More professional.",
    jd_requirement="Professional summary clarity",
    evidence_status="supported",
    evidence_note="No new tools.",
)
session_a.add_suggestion(s3)
s3_id = s3.suggestion_id

session_a.accept_suggestion(s3_id, custom_edit="Passionate Python developer specializing in AI and RAG systems.")
approved3 = session_a.build_approved_resume()
check("Custom edit overrides AI suggestion (summary)",
      approved3.get("summary") == "Passionate Python developer specializing in AI and RAG systems.",
      f"got: {approved3.get('summary')}")

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 6: Cross-candidate contamination check
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 6: Cross-Candidate Contamination ===")

canonical_b = {
    "candidate_name": "Bob Engineer",
    "summary": "Java developer specializing in Spring Boot.",
    "projects": [
        {
            "id": "proj_0",
            "name": "Indexify",
            "description": "Personal Repository Manager",
            "highlights": ["Built a full-stack repository management platform with JWT authentication."],
            "technologies": ["React.js", "Node.js", "Express.js", "MySQL"],
        }
    ],
    "skills": {
        "technical": ["Java", "C++"],
        "frameworks": ["Spring Boot"],
        "cloud": ["AWS"],
        "tools": ["Jira"],
        "databases": [],
        "cybersecurity": [],
        "soft": [],
        "other": [],
    }
}

session_b = create_session("sess_b", copy.deepcopy(canonical_b))

# Session A accepts changes — session B should be unaffected
sa = get_session("sess_a")
sb = get_session("sess_b")

check("Session A exists independently", sa is not None)
check("Session B exists independently", sb is not None)
check("Session A candidate name is Alice Dev",
      sa.original_canonical.get("candidate_name") == "Alice Dev")
check("Session B candidate name is Bob Engineer",
      sb.original_canonical.get("candidate_name") == "Bob Engineer")

# Approved resumes are independent
approved_a_final = sa.build_approved_resume()
approved_b_final = sb.build_approved_resume()

# Alice's projects should not contain Indexify
a_proj_names = [p.get("name") for p in approved_a_final.get("projects", [])]
b_proj_names = [p.get("name") for p in approved_b_final.get("projects", [])]

check("Alice's approved resume does NOT contain Bob's projects",
      "Indexify" not in a_proj_names, f"found: {a_proj_names}")
check("Bob's approved resume does NOT contain Alice's projects",
      "ISO Audit AI" not in b_proj_names, f"found: {b_proj_names}")
check("Bob's approved resume does NOT contain Alice's skills",
      "Python" not in (approved_b_final.get("skills") or {}).get("technical", []),
      f"Bob's skills.technical: {(approved_b_final.get('skills') or {}).get('technical')}")

# ─────────────────────────────────────────────────────────────────────────────
# SUITE 7: Fresher resume (missing optional sections)
# ─────────────────────────────────────────────────────────────────────────────
print("\n=== SUITE 7: Fresher Resume (Missing Optional Sections) ===")
from app.models.canonical_resume import CanonicalResume, Profile

fresher = CanonicalResume()
fresher.profile = Profile(name="Junior Dev", email="junior@example.com")
# No experience, no certifications, no summary — minimal
fresher.skills = CategorizedSkills(technical=["Python"], frameworks=["FastAPI"])
fresher.projects = [
    ProjectItem(
        name="Demo App",
        description="A simple demo application",
        highlights=["Built a REST API using FastAPI."],
        technologies=["Python", "FastAPI"],
    )
]

md_fresher = canonical_to_markdown(fresher)
check("Fresher markdown renders without crashing", len(md_fresher) > 0)
check("Fresher name is present", "Junior Dev" in md_fresher)
check("Fresher project renders", "Demo App" in md_fresher)
# New format: subtitle inline in heading with em-dash
check("Fresher project has subtitle in heading",
      "A simple demo application" in md_fresher)
check("No empty Experience section in fresher resume", "## Work Experience" not in md_fresher)
check("No empty Certifications section in fresher resume", "## Certifications" not in md_fresher)

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
def test_all_layer_e():
    print("\n" + "=" * 68)
    total = PASS + FAIL
    print(f"Results: {PASS}/{total} passed, {FAIL} failed")
    if FAIL == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"FAILED: {FAIL} test(s) need attention (see FAIL lines above)")
    assert FAIL == 0, f"{FAIL} test(s) failed"

if __name__ == "__main__":
    test_all_layer_e()
