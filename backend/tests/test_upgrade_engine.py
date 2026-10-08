from pathlib import Path
import sys
import types
import numpy as np

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# Stub SentenceTransformer to make tests fast & offline
def _make_stub_sentence_transformer():
    class _StubST:
        def encode(self, sentences, *args, **kwargs):
            n = len(sentences) if isinstance(sentences, list) else 1
            arr = np.zeros((n, 32), dtype=np.float32)
            arr[:, -1] = 1.0
            return arr

    class _StubModule(types.ModuleType):
        SentenceTransformer = _StubST

    stub_mod = _StubModule("sentence_transformers")
    stub_mod.SentenceTransformer = _StubST
    return stub_mod

sys.modules.setdefault("sentence_transformers", _make_stub_sentence_transformer())

for _mod_name in ["chromadb", "torch", "transformers", "aiohttp"]:
    if _mod_name not in sys.modules:
        sys.modules[_mod_name] = types.ModuleType(_mod_name)

import pytest
from unittest.mock import patch
from app.generation.resume_upgrade_engine import resume_upgrade_engine
from app.generation.suggestion_manager import get_session


def test_hallucination_guard_with_mocked_rewrite_bullets():
    """
    Test with a mocked rewrite_bullets that adds 'Kubernetes' and '40%':
    - Assert the status is not 'supported' (unsupported or needs_confirmation).
    - Assert the export (build_approved_resume) keeps the original text.
    - Assert the keyword list stays out of the exported canonical.
    """
    resume = {
        "candidate_name": "Jane Developer",
        "profile": {"name": "Jane Developer"},
        "summary": "Full stack engineer experienced in Python and PostgreSQL.",
        "skills": {
            "technical": ["Python", "PostgreSQL", "FastAPI"]
        },
        "experience": [
            {
                "id": "exp_0",
                "role": "Software Engineer",
                "company": "Acme Corp",
                "highlights": [
                    "Engineered RESTful microservices and optimized PostgreSQL database queries."
                ]
            }
        ],
        "projects": [
            {
                "id": "proj_0",
                "name": "Task Manager",
                "description": "Web task manager built with FastAPI and PostgreSQL.",
                "technologies": ["FastAPI", "PostgreSQL"],
                "highlights": [
                    "Implemented background task scheduling pipeline for real-time notifications."
                ]
            }
        ]
    }
    jd_text = "Looking for a Kubernetes and Cloud DevOps Engineer to scale microservices."

    # Mock rewrite_bullets to add "Kubernetes" and "40%"
    async def mock_rewrite(bullets, jd_keywords):
        return {
            b["id"]: b["text"] + " Deployed on Kubernetes clusters improving performance by 40%."
            for b in bullets
        }

    with patch("app.generation.resume_upgrade_engine.rewrite_bullets", side_effect=mock_rewrite):
        result = resume_upgrade_engine.generate_suggestions(resume, jd_text)
        session_id = result["session_id"]
        session = get_session(session_id)

        assert session is not None, "UpgradeSession was not created"
        assert len(session.suggestions) > 0, "No suggestions were generated"

        # Check suggestions
        for sug in session.suggestions:
            if "Kubernetes" in sug.suggested_text or "40%" in sug.suggested_text:
                assert sug.evidence_status != "supported", (
                    f"Expected status != 'supported' for hallucinated suggestion, got '{sug.evidence_status}'"
                )
                assert sug.evidence_status in ("unsupported", "needs_confirmation")

        # Accept all suggestions (even unsupported ones without manual edit)
        for sug in session.suggestions:
            session.accept(sug.id)

        approved = session.build_approved_resume()

        # Assert the export keeps the original text for unsupported suggestions
        for sug in session.suggestions:
            if sug.evidence_status == "unsupported":
                approved_text = str(approved)
                assert sug.suggested_text not in approved_text, (
                    "Unsupported suggested text must not appear in the approved resume export"
                )

        # Assert Kubernetes and 40% are not in the approved export
        approved_exp_bullet = approved["experience"][0]["highlights"][0]
        assert "Kubernetes" not in approved_exp_bullet
        assert "40%" not in approved_exp_bullet
        assert approved_exp_bullet == "Engineered RESTful microservices and optimized PostgreSQL database queries."

        # The keyword list stays out of the exported canonical
        all_exported_skills = []
        for v in (approved.get("skills") or {}).values():
            if isinstance(v, list):
                all_exported_skills.extend([str(s).lower() for s in v])
        assert "kubernetes" not in all_exported_skills
        assert "suggested_skills_to_verify" not in approved
        assert any(k.lower() == "kubernetes" for k in session.suggested_skills_to_verify)
