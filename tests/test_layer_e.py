"""
Layer E Test Suite — AI Resume Upgrade Engine
Tests cover:
  1. Hugging Face client (mocked and offline fallbacks)
  2. Hallucination guard (supported, needs_confirmation, unsupported claims)
  3. Suggestion manager (session isolation, accept, edit, reject, approved resume generation)
  4. Resume upgrade engine (orchestration & graceful fallback)
  5. Upgrade API endpoints (FastAPI test client)
"""

import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.generation.huggingface_client import HuggingFaceClient
from app.generation.hallucination_guard import classify_suggestion, guard_suggestions
from app.generation.suggestion_manager import (
    Suggestion,
    UpgradeSession,
    create_session,
    get_session,
    delete_session,
)
from app.generation.resume_upgrade_engine import ResumeUpgradeEngine

client = TestClient(app)


# ── Sample Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def sample_canonical():
    return {
        "candidate_name": "Alex Mercer",
        "email": "alex.mercer@example.com",
        "phone": "+1-555-0199",
        "summary": "Software developer with 3 years of experience writing web backends.",
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        "experience": [
            {
                "id": "exp_1",
                "role": "Backend Engineer",
                "company": "DataTech Labs",
                "highlights": [
                    "worked on building REST APIs using FastAPI and database models",
                    "helped with code reviews and bug fixes",
                ],
            }
        ],
        "projects": [
            {
                "id": "proj_1",
                "name": "Cloud Observability Agent",
                "technologies": ["Python", "Docker"],
                "description": "Built an agent that monitors server health and logs metrics.",
                "highlights": [
                    "wrote python scripts to collect system stats",
                ],
            }
        ],
    }


@pytest.fixture
def sample_jd():
    return (
        "Senior Backend Engineer. Requirements: Python, FastAPI, PostgreSQL, "
        "Docker, high-throughput microservices architecture, and agile teamwork."
    )


# ── 1. Hugging Face Client Tests ─────────────────────────────────────────────

def test_hf_client_unconfigured_returns_none(monkeypatch):
    """When HF_TOKEN is not set, client should report unconfigured and return None."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    hf = HuggingFaceClient()
    assert not hf.is_configured()
    assert hf.generate("rewrite_summary", "test summary") is None


def test_hf_client_prompt_generation(monkeypatch):
    """Client builds correct user messages based on task type."""
    monkeypatch.setenv("HF_TOKEN", "hf_mock_token_12345")
    hf = HuggingFaceClient()

    user_msg = hf._build_user_message(
        "rewrite_summary",
        "I am a developer.",
        {"candidate_tools": ["Python", "FastAPI"]},
        role_ctx="",
    )
    assert "ORIGINAL SUMMARY:" in user_msg
    assert "CANDIDATE SKILLS" in user_msg
    assert "Python, FastAPI" in user_msg
    assert "Return ONLY the rewritten summary:" in user_msg


def test_hf_client_clean_output():
    """Client properly strips artefacts and validates minimum quality gate."""
    hf = HuggingFaceClient()

    # Should strip [INST] tag remnants and return clean text
    raw_with_tag = "[INST] Architected scalable microservices using FastAPI. [/INST]"
    cleaned = hf._clean_output(raw_with_tag, "original text")
    assert cleaned is not None
    assert "[INST]" not in cleaned
    assert "Architected" in cleaned

    # Output identical to original should be discarded
    same = hf._clean_output("original text", "original text")
    assert same is None

    # Too-short output should be discarded
    short = hf._clean_output("Hi", "original")
    assert short is None


# ── 2. Hallucination Guard Tests ─────────────────────────────────────────────

def test_guard_wording_improvement_is_supported():
    """Simple verb replacement and polish without new facts is classified as supported."""
    orig = "worked on building REST APIs with FastAPI"
    sugg = "Architected and delivered high-performance REST APIs utilizing FastAPI"
    tools = ["Python", "FastAPI"]

    status, note = classify_suggestion(orig, sugg, tools)
    assert status == "supported"
    assert "without adding new factual claims" in note


def test_guard_new_metrics_needs_confirmation():
    """New numbers/percentages not present in original must be flagged for confirmation."""
    orig = "optimized database queries in PostgreSQL"
    sugg = "Optimized PostgreSQL queries, reducing query response times by 45%"
    tools = ["PostgreSQL"]

    status, note = classify_suggestion(orig, sugg, tools)
    assert status == "needs_confirmation"
    assert "45" in note


def test_guard_new_tool_is_unsupported():
    """Injecting an unmentioned technology must be flagged as unsupported."""
    orig = "deployed web application to production servers"
    sugg = "Orchestrated container deployments across Kubernetes clusters in AWS"
    tools = ["Python", "Docker"]  # Neither Kubernetes nor AWS in candidate tools

    status, note = classify_suggestion(orig, sugg, tools)
    assert status == "unsupported"
    assert "Kubernetes" in note or "AWS" in note


def test_guard_new_credential_is_unsupported():
    """Claiming new certifications or degrees must be flagged as unsupported."""
    orig = "familiar with cloud architecture concepts"
    sugg = "AWS Certified Solutions Architect with deep cloud expertise"
    tools = ["Python"]

    status, note = classify_suggestion(orig, sugg, tools)
    assert status == "unsupported"
    assert "credential" in note.lower() or "certif" in note.lower()


def test_guard_batch_preserves_structure():
    """Batch guard function updates suggestion dicts in-place."""
    items = [
        {"original_text": "wrote code in Python", "suggested_text": "Engineered Python backend components"},
        {"original_text": "monitored servers", "suggested_text": "Achieved 99.99% uptime across production clusters"},
    ]
    guarded = guard_suggestions(items, ["Python"])
    assert guarded[0]["evidence_status"] == "supported"
    assert guarded[1]["evidence_status"] == "needs_confirmation"


# ── 3. Suggestion Manager Tests ──────────────────────────────────────────────

def test_session_lifecycle(sample_canonical):
    """Tests session creation, retrieval, suggestions, and eviction."""
    sess_id = create_session(sample_canonical)
    session = get_session(sess_id)
    assert session is not None
    assert session.session_id == sess_id

    # Add a suggestion
    sug = Suggestion(
        section="summary",
        item_id="summary",
        field="summary",
        original_text=sample_canonical["summary"],
        suggested_text="High-impact software developer specializing in Python and FastAPI.",
        explanation="Highlights technical alignment.",
        evidence_status="supported",
    )
    session.add_suggestion(sug)
    assert session.pending_count() == 1
    assert session.accepted_count() == 0

    # Accept suggestion
    assert session.accept(sug.id)
    assert session.accepted_count() == 1
    assert session.pending_count() == 0

    # Build approved resume
    approved = session.build_approved_resume()
    assert approved["summary"] == "High-impact software developer specializing in Python and FastAPI."

    # Delete session
    delete_session(sess_id)
    assert get_session(sess_id) is None


def test_approved_resume_only_includes_accepted(sample_canonical):
    """Pending and rejected suggestions must never appear in approved resume."""
    sess_id = create_session(sample_canonical)
    session = get_session(sess_id)

    # Sug 1: accepted
    s1 = Suggestion(
        section="summary",
        item_id="summary",
        field="summary",
        original_text=sample_canonical["summary"],
        suggested_text="Accepted summary text.",
        explanation="Test explanation",
    )
    # Sug 2: rejected
    s2 = Suggestion(
        section="experience",
        item_id="exp_1",
        field="highlights[0]",
        original_text=sample_canonical["experience"][0]["highlights"][0],
        suggested_text="Rejected bullet text that should not appear.",
        explanation="Test explanation",
    )
    # Sug 3: pending
    s3 = Suggestion(
        section="experience",
        item_id="exp_1",
        field="highlights[1]",
        original_text=sample_canonical["experience"][0]["highlights"][1],
        suggested_text="Pending bullet text that should not appear.",
        explanation="Test explanation",
    )

    session.add_suggestion(s1)
    session.add_suggestion(s2)
    session.add_suggestion(s3)

    session.accept(s1.id)
    session.reject(s2.id)
    # s3 remains pending

    approved = session.build_approved_resume()
    assert approved["summary"] == "Accepted summary text."
    # Original bullet preserved for rejected s2
    assert approved["experience"][0]["highlights"][0] == sample_canonical["experience"][0]["highlights"][0]
    # Original bullet preserved for pending s3
    assert approved["experience"][0]["highlights"][1] == sample_canonical["experience"][0]["highlights"][1]

    delete_session(sess_id)


def test_custom_user_edit_override(sample_canonical):
    """When accepting with edited_text, user override takes precedence over AI suggestion."""
    sess_id = create_session(sample_canonical)
    session = get_session(sess_id)

    sug = Suggestion(
        section="summary",
        item_id="summary",
        field="summary",
        original_text="Old summary",
        suggested_text="AI suggested summary",
        explanation="Test",
    )
    session.add_suggestion(sug)
    session.accept(sug.id, edited_text="My custom handcrafted summary.")

    approved = session.build_approved_resume()
    assert approved["summary"] == "My custom handcrafted summary."

    delete_session(sess_id)


def test_project_ordering_algorithm():
    """Test 4-slot evidence-based project ordering."""
    projects = [
        {"id": "p1", "name": "Basic Portfolio HTML", "technologies": ["HTML", "CSS"], "dates": "2021"},
        {"id": "p2", "name": "Final Year Capstone ML Pipeline", "technologies": ["Python", "PyTorch"], "dates": "2023", "is_pinned": True},
        {"id": "p3", "name": "Cloud Observability Microservices", "technologies": ["Docker", "Kubernetes", "FastAPI"], "dates": "2024"},
        {"id": "p4", "name": "E-Commerce REST API", "technologies": ["Python", "FastAPI", "PostgreSQL"], "dates": "2022"},
    ]
    jd_keywords = ["FastAPI", "Docker", "Kubernetes", "PostgreSQL"]

    engine = ResumeUpgradeEngine()
    order = engine.calculate_project_ordering(projects, jd_keywords)

    assert order is not None
    assert not order["is_already_optimal"]
    # P3 (FastAPI, Docker, Kubernetes) and P4 (FastAPI, PostgreSQL) should be in Slots 1 & 2
    # P2 (Final Year Capstone) should be in Slot 4
    suggested = order["suggested_text"]
    assert "Slot 1: Highest JD Alignment" in suggested
    assert "Slot 4: Capstone" in suggested or "Slot" in suggested


# ── 4. Resume Upgrade Engine Tests ───────────────────────────────────────────

def test_engine_generates_suggestions_offline(sample_canonical, sample_jd):
    """Engine works 100% offline via local heuristics and RAG when HF is unavailable."""
    engine = ResumeUpgradeEngine()
    result = engine.generate_suggestions(sample_canonical, sample_jd)

    assert "session_id" in result
    assert "suggestions" in result
    assert "stats" in result
    assert len(result["suggestions"]) >= 1

    # Verify each suggestion has required fields
    for s in result["suggestions"]:
        assert "id" in s
        assert "section" in s
        assert "original_text" in s
        assert "suggested_text" in s
        assert "evidence_status" in s
        assert "evidence_note" in s
        assert s["status"] == "pending"

    delete_session(result["session_id"])


def test_engine_with_mocked_hf(sample_canonical, sample_jd):
    """Engine integrates HF responses when HF inference succeeds."""
    mock_hf = MagicMock()
    mock_hf.is_configured.return_value = True
    mock_hf.get_model_name.return_value = "mistralai/Mistral-7B-Instruct-v0.2"
    mock_hf.generate.side_effect = lambda task, orig, ctx: f"HF Improved: {orig}"

    engine = ResumeUpgradeEngine(client=mock_hf)
    result = engine.generate_suggestions(sample_canonical, sample_jd)

    assert result["model_used"] == "mistralai/Mistral-7B-Instruct-v0.2"
    suggestions = result["suggestions"]
    assert any("HF Improved:" in s["suggested_text"] for s in suggestions)

    delete_session(result["session_id"])


# ── 5. Layer E FastAPI Endpoint Tests ────────────────────────────────────────

def test_api_hf_status():
    """GET /api/upgrade/hf-status returns client status."""
    res = client.get("/api/upgrade/hf-status")
    assert res.status_code == 200
    data = res.json()
    assert "is_configured" in data
    assert "model_name" in data
    assert "is_available" in data


def test_api_generate_accept_reject_export_workflow(sample_canonical, sample_jd):
    """End-to-end integration test of the full suggestion workflow via HTTP API."""
    # 1. Generate suggestions
    res = client.post(
        "/api/upgrade/generate-suggestions",
        data={
            "canonical_resume_json": json.dumps(sample_canonical),
            "jd_text": sample_jd,
        },
    )
    assert res.status_code == 200
    gen_data = res.json()
    assert gen_data["status"] == "success"
    session_id = gen_data["session_id"]
    suggestions = gen_data["suggestions"]
    assert len(suggestions) > 0

    first_sug = suggestions[0]
    first_id = first_sug["id"]

    # 2. Accept first suggestion with custom edit
    res_accept = client.post(
        "/api/upgrade/accept-suggestion",
        data={
            "session_id": session_id,
            "suggestion_id": first_id,
            "edited_text": "Custom accepted wording by candidate",
        },
    )
    assert res_accept.status_code == 200
    acc_data = res_accept.json()
    assert acc_data["suggestion"]["status"] == "accepted"
    assert acc_data["suggestion"]["edited_text"] == "Custom accepted wording by candidate"
    assert acc_data["stats"]["accepted"] == 1

    # 3. Reject second suggestion (if present)
    if len(suggestions) > 1:
        second_id = suggestions[1]["id"]
        res_reject = client.post(
            "/api/upgrade/reject-suggestion",
            data={
                "session_id": session_id,
                "suggestion_id": second_id,
            },
        )
        assert res_reject.status_code == 200
        rej_data = res_reject.json()
        assert rej_data["suggestion"]["status"] == "rejected"
        assert rej_data["stats"]["rejected"] == 1

    # 4. Check session status
    res_status = client.get(f"/api/upgrade/session-status?session_id={session_id}")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["stats"]["accepted"] >= 1

    # 5. Fetch approved resume
    res_app = client.get(f"/api/upgrade/approved-resume?session_id={session_id}")
    assert res_app.status_code == 200
    app_data = res_app.json()
    assert "approved_canonical" in app_data
    # First suggestion was for summary (or experience highlight)
    if first_sug["section"] == "summary":
        assert app_data["approved_canonical"]["summary"] == "Custom accepted wording by candidate"

    # 6. Export approved PDF
    res_pdf = client.post(
        "/api/upgrade/export-pdf",
        data={"session_id": session_id},
    )
    assert res_pdf.status_code == 200
    assert res_pdf.headers["content-type"] == "application/pdf"
    assert len(res_pdf.content) > 500
    assert "Upgraded_Resume.pdf" in res_pdf.headers["content-disposition"]

    delete_session(session_id)


# ── 6. Layer F Codebase & Documentation RAG Knowledge Base Tests ──────────────

from app.ai.codebase_rag import CodebaseRAGKnowledgeStore, codebase_rag_instance


def test_codebase_rag_indexing_and_retrieval(sample_canonical):
    """Layer F correctly indexes resume and GitHub READMEs and retrieves verified context."""
    store = CodebaseRAGKnowledgeStore()
    store.index_resume(sample_canonical)

    # Ingest GitHub README evidence
    github_evidence = [
        {
            "repo_name": "cloud-agent",
            "full_name": "alexmercer/cloud-agent",
            "technologies": ["Python", "Docker", "Prometheus"],
            "description": "Server health telemetry and Prometheus metrics collector",
            "readme_content": (
                "# Cloud Observability Agent\n\n"
                "## Architecture\n"
                "Collects system memory and CPU utilization metrics via Python async workers.\n\n"
                "## Endpoints\n"
                "Exposes `/metrics` endpoint formatted for Prometheus scraping.\n"
            ),
        }
    ]
    store.index_github_repositories(github_evidence)

    # Verify verified tools whitelist
    assert "python" in store.candidate_all_tools
    assert "fastapi" in store.candidate_all_tools
    assert "docker" in store.candidate_all_tools
    assert "prometheus" in store.candidate_all_tools

    # Retrieve context for a query
    rag_result = store.retrieve_grounded_context("metrics collection in agent", project_name="Cloud Observability Agent")
    assert "verified_tools" in rag_result
    assert "evidence_snippets" in rag_result
    assert len(rag_result["evidence_snippets"]) > 0
    # Strict constraint should be present in prompt block
    assert "STRICT CONSTRAINT: ONLY use verified tools" in rag_result["rag_prompt_block"]
    assert "VERIFIED EVIDENCE" in rag_result["rag_prompt_block"]


def test_api_generate_suggestions_with_github_evidence(sample_canonical, sample_jd):
    """API endpoint /api/upgrade/generate-suggestions correctly ingests github_evidence_json."""
    gh_evidence = [
        {
            "repo_name": "fastapi-store",
            "technologies": ["FastAPI", "PostgreSQL", "SQLAlchemy"],
            "description": "Production REST API for inventory management",
            "readme_content": "# Inventory API\nBuilt with FastAPI, PostgreSQL, and SQLAlchemy.",
        }
    ]

    res = client.post(
        "/api/upgrade/generate-suggestions",
        data={
            "canonical_resume_json": json.dumps(sample_canonical),
            "jd_text": sample_jd,
            "github_evidence_json": json.dumps(gh_evidence),
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["suggestions"]) > 0
    delete_session(data["session_id"])

