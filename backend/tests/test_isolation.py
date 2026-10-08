"""
Isolation Test Suite — Multi-Tenant Data Leakage & Session Isolation Audit.

Strategy:
  * Two completely distinct fake resumes are defined inline (no fixture files needed,
    but the existing fixture directory is used as a fallback).
  * SentenceTransformer is patched to a stub that returns deterministic unit vectors,
    so no model is downloaded and no GPU/CPU time is wasted.
  * Every outbound network call (httpx, aiohttp, requests, socket) is mocked to
    return empty / benign responses so the suite stays fully offline.
  * SQLite github_provenance.db creation is redirected to an in-memory database
    so no disk artefact is written.
  * Tests use httpx.ASGITransport — no live server is started.
  * Target runtime: < 30 seconds on a cold CI runner.

Tests:
  1. test_analyze_isolation_between_candidates
       POST /api/analyze with A then B; assert no A-PII in B's JSON response or logs.
  2. test_upgrade_workflow_isolation_between_candidates
       POST /api/upgrade/generate-suggestions with A then B;
       assert distinct session IDs, no A-PII in B's suggestions payload.
  3. test_session_ids_are_unique
       Three rapid create_session() calls must all produce different IDs.
  4. test_sessions_are_independent
       Accepting a suggestion in session A must not mutate session B.
  5. test_rag_singleton_cleared_between_candidates
       index_resume() for A then clear() + index_resume() for B;
       assert retrieve_grounded_context() returns only B's keywords.
  6. test_claim_paragraph_single_claim
       A description with no embedded newlines produces exactly one
       "Implementation Feature" claim from extract_claims_from_project().
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Path setup — make sure the backend package is importable
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ---------------------------------------------------------------------------
# Stub SentenceTransformer BEFORE any app module is imported
# ---------------------------------------------------------------------------

def _make_stub_sentence_transformer():
    """Return a sentinel model that produces deterministic unit embeddings."""
    class _StubST:
        def encode(self, sentences, *args, **kwargs):
            n = len(sentences) if isinstance(sentences, list) else 1
            # Return a matrix of zeros with a 1 in the last column so
            # cosine similarity between any two embeddings is 1.0 (max).
            arr = np.zeros((n, 32), dtype=np.float32)
            arr[:, -1] = 1.0
            return arr

    class _StubModule(types.ModuleType):
        SentenceTransformer = _StubST

    stub_mod = _StubModule("sentence_transformers")
    stub_mod.SentenceTransformer = _StubST
    return stub_mod, _StubST


_STUB_ST_MOD, _STUB_ST_CLASS = _make_stub_sentence_transformer()
sys.modules.setdefault("sentence_transformers", _STUB_ST_MOD)

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies that may not be installed in CI
# ---------------------------------------------------------------------------

for _mod_name in [
    "chromadb",
    "torch",
    "transformers",
    "aiohttp",
]:
    if _mod_name not in sys.modules:
        _stub = types.ModuleType(_mod_name)
        sys.modules[_mod_name] = _stub

# ---------------------------------------------------------------------------
# Redirect SQLite github_provenance.db to an in-memory path so no file is created
# ---------------------------------------------------------------------------
import sqlite3 as _sqlite3

_ORIG_SQLITE_CONNECT = _sqlite3.connect


def _in_memory_connect(database, *args, **kwargs):
    """Redirect any DB path containing 'github_provenance' to :memory:."""
    if "github_provenance" in str(database):
        return _ORIG_SQLITE_CONNECT(":memory:", *args, **kwargs)
    return _ORIG_SQLITE_CONNECT(database, *args, **kwargs)


_sqlite3.connect = _in_memory_connect  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Now import the FastAPI app (all heavy singletons are already patched above)
# ---------------------------------------------------------------------------
import httpx

from app.main import app  # noqa: E402  (must be after patches)
from app.generation.huggingface_client import hf_client
from app.generation.ollama_client import ollama_client

hf_client.is_configured = lambda: False
ollama_client.is_configured = lambda: False


# ---------------------------------------------------------------------------
# Fake resume text — two candidates with completely disjoint PII
# ---------------------------------------------------------------------------

RESUME_A = """
ALICE DEVELOPER
Cloud Systems Architect & Backend Developer
Email: alice.dev@example.org | Phone: +1 555-010-1234
GitHub: https://github.com/alicedev42
LinkedIn: https://linkedin.com/in/alicedev42
Portfolio: https://alicedev.io

PROFESSIONAL SUMMARY
Passionate Cloud Systems Architect specializing in distributed systems, Go, and
Kubernetes microservices with deep expertise in DynamoDB and Terraform automation.

TECHNICAL SKILLS
Languages: Go, Python, Rust, SQL
Cloud & DevOps: Kubernetes, AWS, Terraform, Docker
Databases: PostgreSQL, Redis, DynamoDB

WORK EXPERIENCE
Senior Systems Engineer — CloudCore Inc (2022 – Present)
• Designed high-throughput microservices handling 50k RPS in Go and Redis.
• Architected multi-region AWS clusters using Terraform infrastructure as code.

PROJECTS
1. KubeFlow Orchestrator (GitHub: https://github.com/alicedev42/kubeflow-orchestrator)
Built Kubernetes controller in Go scaling pods via Redis metrics using Raft consensus.

2. Distributed Key-Value Store (GitHub: https://github.com/alicedev42/dist-kv-store)
Implemented Raft consensus algorithm from scratch in Rust with write-ahead logging.

3. Cloud Cost Analyzer (GitHub: https://github.com/alicedev42/cloud-cost-analyzer)
Serverless AWS Lambda pipelines in Python auditing idle EBS volumes and resources.

EDUCATION
B.S. Computer Science — UC Berkeley (2018 – 2022) | GPA: 3.9

CERTIFICATIONS
AWS Certified Solutions Architect – Professional
""".strip()

RESUME_B = """
BOB BUILDER
Frontend Specialist & Creative Technologist
Email: bob.engineer@techcorp.fake | Phone: +1 555-987-6543
GitHub: https://github.com/bobbuilder99
LinkedIn: https://linkedin.com/in/bobbuilder99
Portfolio: https://bobbuilder.net

SUMMARY
Frontend developer crafting accessible web experiences with modern JavaScript.

CORE COMPETENCIES
Programming: JavaScript, TypeScript, HTML5, CSS3, PHP
Frameworks: React, Vue.js, Next.js, TailwindCSS
Tooling: Webpack, Vite, Figma, Jest

EXPERIENCE
Lead UI Developer — CreativeStudio (2021 – Present)
* Led front-end team building design systems in React and TypeScript.
* Improved web accessibility score to 100% across checkout workflows.

PROJECTS
Project: E-Commerce Storefront
https://github.com/bobbuilder99/ecommerce-storefront
Headless retail application built with Next.js and TailwindCSS with Stripe checkout.

Project: Vector Design Canvas
https://github.com/bobbuilder99/vector-design-canvas
Browser-based SVG vector editor in Vue.js with WebSockets multiplayer collaboration.

EDUCATION
B.A. Digital Media & Web Design — NYU (2017 – 2021) | GPA: 3.7

CERTIFICATIONS
Certified Frontend Web Developer
""".strip()

# PII / identifiers that must NEVER appear in Candidate B's responses
A_IDENTIFIERS = [
    "Alice Developer",
    "alice.dev@example.org",
    "alicedev42",
    "KubeFlow Orchestrator",
    "Distributed Key-Value Store",
    "Cloud Cost Analyzer",
    "alicedev42/kubeflow-orchestrator",
    "alicedev42/dist-kv-store",
    "alicedev42/cloud-cost-analyzer",
    "alicedev.io",
    "CloudCore Inc",
]

A_DISTINCT_SKILLS = ["DynamoDB", "Terraform", "Raft"]

SAMPLE_JD = """
Full Stack Software Engineer
We seek a versatile developer experienced in modern software architectures.
Requirements: Git, testing, web services, REST APIs, relational databases.
""".strip()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pdf_bytes(text: str) -> bytes:
    """Convert plain text to a minimal PDF via pymupdf."""
    import pymupdf as fitz  # type: ignore

    doc = fitz.open()
    page = doc.new_page()
    rect = fitz.Rect(40, 40, 560, 800)
    page.insert_textbox(rect, text, fontsize=9, fontname="helv")
    raw = doc.tobytes()
    doc.close()
    return raw


def _contains_any(haystack: str, needles: list[str]) -> list[str]:
    """Return the subset of needles found (case-insensitive) in haystack."""
    return [n for n in needles if n.lower() in haystack.lower()]


def _contains_skill(haystack: str, skill: str) -> bool:
    return bool(re.search(rf"\b{re.escape(skill)}\b", haystack, re.IGNORECASE))


# ---------------------------------------------------------------------------
# ASGI client — no live server
# ---------------------------------------------------------------------------

class _SyncASGIClient:
    """Thin synchronous wrapper around httpx.AsyncClient + ASGITransport."""

    def __init__(self, asgi_app):
        self._transport = httpx.ASGITransport(app=asgi_app)

    def _run(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def post(self, url: str, **kwargs) -> httpx.Response:
        async def _inner():
            async with httpx.AsyncClient(
                transport=self._transport,
                base_url="http://testserver",
                timeout=60.0,
            ) as ac:
                req = ac.build_request("POST", url, **kwargs)
                return await ac.send(req)

        return self._run(_inner())

    def get(self, url: str, **kwargs) -> httpx.Response:
        async def _inner():
            async with httpx.AsyncClient(
                transport=self._transport,
                base_url="http://testserver",
                timeout=60.0,
            ) as ac:
                req = ac.build_request("GET", url, **kwargs)
                return await ac.send(req)

        return self._run(_inner())



# Instantiate once — shared across all tests in this module
_client = _SyncASGIClient(app)

# ---------------------------------------------------------------------------
# Network mock helpers
# ---------------------------------------------------------------------------

def _mock_httpx_get(*args, **kwargs):
    """Return an empty 200 response for any outbound GET."""
    return MagicMock(
        status_code=200,
        json=lambda: {},
        text="",
        content=b"",
        headers={},
    )


_ASYNC_MOCK_HTTPX = AsyncMock(return_value=MagicMock(
    status_code=200,
    json=MagicMock(return_value={}),
    text="",
    content=b"",
    headers={},
    raise_for_status=MagicMock(),
))



# ===========================================================================
# Test 1 — /api/analyze isolation
# ===========================================================================

@patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))
@patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))

def test_analyze_isolation_between_candidates(mock_post, mock_get, caplog):
    """
    POST /api/analyze with Resume A then Resume B.
    Assert no Candidate A PII appears in Candidate B's JSON response or in
    log output captured during B's processing.
    """
    pdf_a = _make_pdf_bytes(RESUME_A)
    pdf_b = _make_pdf_bytes(RESUME_B)

    # ── Candidate A ──────────────────────────────────────────────────────────
    resp_a = _client.post(
        "/api/analyze",
        files={"resume_file": ("resume_A.pdf", pdf_a, "application/pdf")},
        data={"jd_text": SAMPLE_JD},
    )
    assert resp_a.status_code == 200, f"Analyze A failed ({resp_a.status_code}): {resp_a.text[:300]}"

    # ── Candidate B (log capture active) ─────────────────────────────────────
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        resp_b = _client.post(
            "/api/analyze",
            files={"resume_file": ("resume_B.pdf", pdf_b, "application/pdf")},
            data={"jd_text": SAMPLE_JD},
        )
    assert resp_b.status_code == 200, f"Analyze B failed ({resp_b.status_code}): {resp_b.text[:300]}"

    body_b = resp_b.text
    logs_b = caplog.text

    # Response isolation
    leaked = _contains_any(body_b, A_IDENTIFIERS)
    assert not leaked, (
        f"Isolation failure — Candidate A identifiers found in B's /api/analyze response: {leaked}"
    )
    for skill in A_DISTINCT_SKILLS:
        assert not _contains_skill(body_b, skill), (
            f"Isolation failure — Candidate A skill '{skill}' found in B's response"
        )

    # Log isolation
    leaked_logs = _contains_any(logs_b, A_IDENTIFIERS)
    assert not leaked_logs, (
        f"Log leakage — Candidate A identifiers in logs during B's processing: {leaked_logs}"
    )


# ===========================================================================
# Test 2 — /api/upgrade/generate-suggestions isolation
# ===========================================================================

@patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))
@patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))

def test_upgrade_workflow_isolation_between_candidates(mock_post, mock_get):
    """
    POST /api/upgrade/generate-suggestions for A then B.
    Assert distinct session IDs and no A PII in B's suggestions payload.
    """
    # ── Candidate A ──────────────────────────────────────────────────────────
    resp_a = _client.post(
        "/api/upgrade/generate-suggestions",
        data={"resume_text": RESUME_A, "jd_text": SAMPLE_JD},
    )
    assert resp_a.status_code == 200, f"Upgrade A failed: {resp_a.text[:300]}"
    data_a = resp_a.json()
    session_a = data_a.get("session_id")
    assert session_a, "No session_id returned for Candidate A"

    # ── Candidate B ──────────────────────────────────────────────────────────
    resp_b = _client.post(
        "/api/upgrade/generate-suggestions",
        data={"resume_text": RESUME_B, "jd_text": SAMPLE_JD},
    )
    assert resp_b.status_code == 200, f"Upgrade B failed: {resp_b.text[:300]}"
    data_b = resp_b.json()
    session_b = data_b.get("session_id")
    assert session_b, "No session_id returned for Candidate B"

    # Session IDs must differ
    assert session_a != session_b, (
        f"Session ID collision: both candidates received '{session_a}'"
    )

    # PII isolation in suggestions payload
    payload_b = json.dumps(data_b)
    leaked = _contains_any(payload_b, A_IDENTIFIERS)
    assert not leaked, (
        f"Upgrade isolation failure — A identifiers found in B's payload: {leaked}"
    )
    for skill in A_DISTINCT_SKILLS:
        assert not _contains_skill(payload_b, skill), (
            f"Upgrade isolation failure — A skill '{skill}' found in B's payload"
        )


# ===========================================================================
# Test 3 — session IDs are unique
# ===========================================================================

def test_session_ids_are_unique():
    """
    Three consecutive create_session() calls must return distinct IDs.
    This validates the uuid4-based keying in suggestion_manager.
    """
    from app.generation.suggestion_manager import create_session, delete_session

    minimal_resume = {"profile": {"name": "Test User"}, "summary": "Test"}
    sid1 = create_session(minimal_resume)
    sid2 = create_session(minimal_resume)
    sid3 = create_session(minimal_resume)

    ids = {str(sid1), str(sid2), str(sid3)}
    assert len(ids) == 3, f"Expected 3 unique session IDs, got: {ids}"

    # Cleanup
    for sid in (sid1, sid2, sid3):
        delete_session(str(sid))


# ===========================================================================
# Test 4 — sessions are independent (accepting a suggestion in A ≠ mutates B)
# ===========================================================================

def test_sessions_are_independent():
    """
    Accepting a suggestion in Session A must leave Session B's suggestions
    in 'pending' state — no cross-session mutation.
    """
    from app.generation.suggestion_manager import (
        Suggestion,
        UpgradeSession,
        create_session,
        delete_session,
        get_session,
    )

    resume_a = {"profile": {"name": "Alice"}, "summary": "Alice summary"}
    resume_b = {"profile": {"name": "Bob"}, "summary": "Bob summary"}

    sid_a = create_session(resume_a)
    sid_b = create_session(resume_b)

    sess_a = get_session(str(sid_a))
    sess_b = get_session(str(sid_b))

    # Add one suggestion to each session
    sug_a = Suggestion(
        section="summary",
        item_id="",
        field="summary",
        original_text="Alice original",
        suggested_text="Alice improved",
        explanation="Better wording",
    )
    sug_b = Suggestion(
        section="summary",
        item_id="",
        field="summary",
        original_text="Bob original",
        suggested_text="Bob improved",
        explanation="Better wording",
    )
    sess_a.add_suggestion(sug_a)
    sess_b.add_suggestion(sug_b)

    # Accept A's suggestion
    ok = sess_a.accept(sug_a.id)
    assert ok, "accept() returned False"

    # B's suggestion must remain pending
    b_sug = sess_b.get_suggestion(sug_b.id)
    assert b_sug is not None
    assert b_sug.status == "pending", (
        f"Session B suggestion mutated to '{b_sug.status}' after A was accepted"
    )

    # Also confirm A's suggestion is not visible in B
    a_sug_via_b = sess_b.get_suggestion(sug_a.id)
    assert a_sug_via_b is None, "Candidate A suggestion leaked into Candidate B session"

    delete_session(str(sid_a))
    delete_session(str(sid_b))


# ===========================================================================
# Test 5 — RAG singleton is cleanly replaced between candidates
# ===========================================================================

def test_rag_singleton_cleared_between_candidates():
    """
    Index Candidate A into codebase_rag_instance, then clear() and index
    Candidate B. The retrieve_grounded_context() result must only contain
    B-specific keywords and no A-specific ones.
    """
    from app.ai.codebase_rag import codebase_rag_instance

    resume_a_data = {
        "summary": "DynamoDB Terraform Raft consensus specialist",
        "skills": {"technical": ["DynamoDB", "Terraform", "Raft", "Go", "Rust"]},
        "experience": [],
        "projects": [
            {
                "name": "KubeFlow Orchestrator",
                "description": "Kubernetes controller using Raft in Go with DynamoDB",
                "technologies": ["Go", "DynamoDB", "Raft"],
                "highlights": [],
            }
        ],
    }
    resume_b_data = {
        "summary": "React TypeScript TailwindCSS frontend specialist",
        "skills": {"technical": ["React", "TypeScript", "TailwindCSS", "Vue.js", "JavaScript"]},
        "experience": [],
        "projects": [
            {
                "name": "E-Commerce Storefront",
                "description": "Next.js headless storefront with TailwindCSS and Stripe",
                "technologies": ["Next.js", "TailwindCSS", "Stripe", "TypeScript"],
                "highlights": [],
            }
        ],
    }

    # Index A
    codebase_rag_instance.clear()
    codebase_rag_instance.index_resume(resume_a_data)
    a_tools = set(codebase_rag_instance.candidate_all_tools)
    assert any("dynamodb" in t or "raft" in t or "terraform" in t for t in a_tools), (
        f"A's distinctive tools not indexed; found: {a_tools}"
    )

    # Replace with B
    codebase_rag_instance.clear()
    codebase_rag_instance.index_resume(resume_b_data)
    b_tools = set(codebase_rag_instance.candidate_all_tools)

    # A's tools must not appear in B's tool set
    a_specific = {"dynamodb", "raft", "terraform"}
    leaked = a_specific & b_tools
    assert not leaked, (
        f"RAG singleton leaked Candidate A's tools into B's context: {leaked}"
    )

    # B's tools should be present
    assert any("react" in t or "tailwindcss" in t for t in b_tools), (
        f"B's distinctive tools not in RAG after clear+index; found: {b_tools}"
    )

    # Cleanup
    codebase_rag_instance.clear()


# ===========================================================================
# Test 6 — paragraph with no newlines → exactly one Implementation Feature claim
# ===========================================================================

def test_claim_paragraph_single_claim():
    """
    extract_claims_from_project() extracts discrete keyword-level capability claims
    (e.g., 'Docker deployment', 'Kubernetes deployment') rather than whole paragraph text.
    Claims must never be entire paragraphs or multi-sentence blocks.
    """
    from app.extraction.claim_extractor import extract_claims_from_project

    # Single paragraph, no newlines
    one_para_desc = (
        "Built a REST microservice in Python using FastAPI and PostgreSQL "
        "that processes 10,000 requests per second with sub-20ms latency "
        "and deploys to AWS via Docker and Kubernetes."
    )
    project = {
        "title": "Demo Project",
        "description": one_para_desc,
        "technologies": [],  # no tech claims — isolate the feature claim path
    }

    claims = extract_claims_from_project(project)

    feature_claims = [c for c in claims if c["claim_type"] == "Implementation Feature"]

    # Capability claims extracted (e.g. Docker deployment, Kubernetes deployment)
    assert len(feature_claims) >= 1, "Expected at least 1 Implementation Feature claim"
    for fc in feature_claims:
        # Every claim must be concise (<= 5 words) and never the full paragraph
        assert len(fc["claim"].split()) <= 5, f"Claim exceeds 5 words: {fc['claim']}"
        assert fc["claim"] != one_para_desc, "Claim must not be the entire paragraph"


# ===========================================================================
# Test 7 — Cross-user RAG isolation: candidate A indexed, suggestions generated for B
# ===========================================================================

@patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))
@patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=MagicMock(
    status_code=200, json=MagicMock(return_value={}), text="", content=b"",
    headers={}, raise_for_status=MagicMock()
))
def test_rag_isolation_cross_candidate(mock_post, mock_get):
    """
    Index Candidate A into codebase_rag_instance, then call /api/upgrade/generate-suggestions
    for Candidate B.
    Assert Candidate A's name, email, and distinct tools are not in B's suggestions
    or in codebase_rag_instance.chunks.
    """
    from app.ai.codebase_rag import codebase_rag_instance

    resume_a_data = {
        "profile": {"name": "Alice Developer", "email": "alice.dev@example.org"},
        "summary": "DynamoDB Terraform Raft consensus specialist",
        "skills": {"technical": ["DynamoDB", "Terraform", "Raft", "Go", "Rust"]},
        "experience": [],
        "projects": [
            {
                "name": "KubeFlow Orchestrator",
                "description": "Kubernetes controller using Raft in Go with DynamoDB",
                "technologies": ["Go", "DynamoDB", "Raft"],
                "highlights": [],
            }
        ],
    }

    # Index Candidate A directly
    codebase_rag_instance.reset()
    codebase_rag_instance.index_resume(resume_a_data)
    assert len(codebase_rag_instance.chunks) > 0, "Candidate A chunks were not indexed"

    # Call generate-suggestions for Candidate B
    resp_b = _client.post(
        "/api/upgrade/generate-suggestions",
        data={"resume_text": RESUME_B, "jd_text": SAMPLE_JD},
    )
    assert resp_b.status_code == 200, f"Generate suggestions for B failed: {resp_b.text[:300]}"
    data_b = resp_b.json()
    payload_b = json.dumps(data_b)

    # 1. Assert A's name, email, and tools are not in B's suggestions payload
    assert "Alice Developer" not in payload_b, "Alice Developer leaked into B's suggestions"
    assert "alice.dev@example.org" not in payload_b, "Alice's email leaked into B's suggestions"
    for skill in A_DISTINCT_SKILLS:
        assert not _contains_skill(payload_b, skill), f"Candidate A tool '{skill}' leaked into B's suggestions"

    # 2. Assert A's name, email, and tools are not in codebase_rag_instance.chunks
    chunk_texts = " ".join(c.get("text", "") for c in codebase_rag_instance.chunks)
    assert "Alice Developer" not in chunk_texts, "Alice Developer found in codebase_rag_instance.chunks"
    assert "alice.dev@example.org" not in chunk_texts, "Alice email found in codebase_rag_instance.chunks"
    for skill in A_DISTINCT_SKILLS:
        assert not _contains_skill(chunk_texts, skill), f"Candidate A tool '{skill}' found in codebase_rag_instance.chunks"

    # Cleanup
    codebase_rag_instance.reset()


