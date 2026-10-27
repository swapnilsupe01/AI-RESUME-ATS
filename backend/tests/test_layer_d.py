"""
Layer D — Unit Tests
=====================
Tests covering: single-commit repo, healthy repo, fork, rate-limit error, missing user.
All GitHub API calls are fully mocked using pytest-mock / unittest.mock.
"""
from __future__ import annotations

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_commit(msg: str, date: str = "2024-03-15T10:00:00Z",
                 login: str = "octocat") -> Dict:
    return {
        "commit": {"message": msg, "author": {"name": "Octocat", "date": date}},
        "author": {"login": login},
    }


def _make_repo(name: str, fork: bool = False, archived: bool = False,
               size: int = 500) -> Dict:
    return {
        "name": name,
        "fork": fork,
        "archived": archived,
        "size": size,
        "default_branch": "main",
        "description": f"Test repo {name}",
        "pushed_at": "2024-03-15T10:00:00Z",
    }


HEALTHY_TREE = [
    "README.md",
    "requirements.txt",
    ".gitignore",
    "src/main.py",
    "tests/test_main.py",
    "Dockerfile",
    ".github/workflows/ci.yml",
    "pytest.ini",
    "LICENSE",
    ".env.example",
]

MINIMAL_TREE = [
    "README.md",
    "main.py",
    ".gitignore",
    "requirements.txt",
]

HEALTHY_COMMITS = [
    _make_commit("feat: add login endpoint", "2024-01-01T09:00:00Z"),
    _make_commit("fix: resolve auth bug", "2024-01-10T11:00:00Z"),
    _make_commit("docs: update README", "2024-01-20T14:00:00Z"),
    _make_commit("test: add unit tests for auth", "2024-02-01T10:00:00Z"),
    _make_commit("feat: add dashboard route", "2024-02-15T16:00:00Z"),
    _make_commit("chore: add CI workflow", "2024-03-01T09:00:00Z"),
    _make_commit("refactor: extract utils module", "2024-03-10T11:00:00Z"),
    _make_commit("fix: handle edge case in parser", "2024-03-15T10:00:00Z"),
]

SINGLE_COMMIT = [_make_commit("initial commit", "2024-03-15T10:00:00Z")]

LAZY_COMMITS = [
    _make_commit("update", "2024-01-01T10:00:00Z"),
    _make_commit("changes", "2024-01-01T10:30:00Z"),
    _make_commit("fix", "2024-01-01T11:00:00Z"),
    _make_commit("done", "2024-01-01T11:30:00Z"),
    _make_commit("final", "2024-01-01T12:00:00Z"),
]

HEALTHY_README = "# My Project\n" + "word " * 350 + "\n## Installation\n\n```bash\npip install -r requirements.txt\n```\n"


# ── checks.py tests ───────────────────────────────────────────────────────────

class TestFileChecks:
    def test_healthy_repo_all_checks_pass(self):
        from app.layer_d.checks import run_file_checks
        results = run_file_checks(HEALTHY_TREE, HEALTHY_README)
        assert results["tests"]["status"] == "present"
        assert results["docker"]["status"] == "present"
        assert results["ci_cd"]["status"] == "present"
        assert results["readme"]["status"] == "present"
        assert results["gitignore"]["status"] == "present"
        assert results["license"]["status"] == "present"
        assert results["env_example"]["status"] == "present"
        assert results["deps"]["status"] == "present"
        assert results["secrets"]["status"] == "pass"

    def test_minimal_repo_missing_advanced_checks(self):
        from app.layer_d.checks import run_file_checks
        results = run_file_checks(MINIMAL_TREE, None)
        assert results["tests"]["status"] == "missing"
        assert results["docker"]["status"] == "missing"
        assert results["ci_cd"]["status"] == "missing"
        assert results["readme"]["status"] == "partial"  # exists but no README text
        assert results["gitignore"]["status"] == "present"
        assert results["deps"]["status"] == "present"
        assert results["secrets"]["status"] == "pass"

    def test_secrets_detected(self):
        from app.layer_d.checks import run_file_checks
        tree_with_secret = [".env", "README.md", "main.py"]
        results = run_file_checks(tree_with_secret, None)
        assert results["secrets"]["status"] == "fail"
        assert results["secrets"]["score"] == -10

    def test_readme_quality_short(self):
        from app.layer_d.checks import run_file_checks
        results = run_file_checks(["README.md"], "Short readme.")
        assert results["readme"]["status"] == "partial"

    def test_readme_quality_full(self):
        from app.layer_d.checks import run_file_checks
        results = run_file_checks(["README.md"], HEALTHY_README)
        assert results["readme"]["status"] == "present"
        assert results["readme"]["score"] == 10


class TestCommitChecks:
    def test_single_commit_instant_dump(self):
        from app.layer_d.checks import run_commit_checks
        result, _ = run_commit_checks(SINGLE_COMMIT, "octocat")
        cc = result["commit_count"]
        assert cc["status"] == "fail"
        assert cc.get("flag") == "instant_dump"
        assert cc["score"] == 0

    def test_healthy_commits_score_high(self):
        from app.layer_d.checks import run_commit_checks
        result, intents = run_commit_checks(HEALTHY_COMMITS, "octocat")
        assert result["commit_count"]["status"] == "present"
        assert result["commit_count"]["score"] == 10
        assert result["time_span"]["score"] >= 3
        # All are conventional → high quality
        assert result["message_quality"]["score"] >= 4

    def test_lazy_commits_flagged(self):
        from app.layer_d.checks import run_commit_checks
        result, intents = run_commit_checks(LAZY_COMMITS, "octocat")
        mq = result["message_quality"]
        assert mq.get("flag") == "generic_commit_messages"

    def test_intent_classification(self):
        from app.layer_d.checks import classify_message
        assert classify_message("feat: add login") == "feat"
        assert classify_message("fix: resolve null pointer") == "fix"
        assert classify_message("docs: update README") == "docs"
        assert classify_message("update") == "lazy"
        assert classify_message("initial commit") == "lazy"
        assert classify_message("random description of work done") == "unknown"


# ── anomaly.py tests ──────────────────────────────────────────────────────────

class TestAnomalyDetection:
    def test_single_commit_is_anomalous(self):
        from app.layer_d.anomaly import run_anomaly_detection
        stats = [{"name": "repo", "commit_count": 1, "active_days": 1,
                   "max_day_share": 1.0, "lazy_ratio": 1.0, "repo_score": 10}]
        result = run_anomaly_detection(stats)
        assert result[0]["anomaly_score"] > 0.7
        assert result[0]["anomaly_label"] == "Suspicious Burst / Dump Pattern"

    def test_healthy_commits_normal_pattern(self):
        from app.layer_d.anomaly import run_anomaly_detection
        stats = [{"name": "repo", "commit_count": 50, "active_days": 90,
                   "max_day_share": 0.05, "lazy_ratio": 0.1, "repo_score": 80}]
        result = run_anomaly_detection(stats)
        assert result[0]["anomaly_label"] == "Normal Developer Pattern"

    def test_burst_pattern_detected(self):
        from app.layer_d.anomaly import run_anomaly_detection
        stats = [{"name": "repo", "commit_count": 8, "active_days": 1,
                   "max_day_share": 0.9, "lazy_ratio": 0.8, "repo_score": 20}]
        result = run_anomaly_detection(stats)
        assert result[0]["anomaly_score"] > 0.7


# ── scoring.py tests ──────────────────────────────────────────────────────────

class TestScoring:
    def test_perfect_file_checks_score(self):
        from app.layer_d.scoring import compute_repo_score
        fc = {k: {"score": v, "max": v, "status": "present"} for k, v in
              [("tests", 15), ("docker", 10), ("ci_cd", 10), ("readme", 10),
               ("deps", 5), ("gitignore", 5), ("license", 3), ("env_example", 5),
               ("test_config", 5), ("e2e", 5), ("secrets", 0), ("template_only", 0)]}
        cc = {"commit_count": {"score": 10, "max": 10, "status": "present"},
              "time_span": {"score": 5, "max": 5, "status": "present"},
              "message_quality": {"score": 7, "max": 7, "status": "present"},
              "author_match": {"score": 5, "max": 5, "status": "present"}}
        score, _ = compute_repo_score(fc, cc)
        assert score == 100

    def test_overall_score_uses_best_5(self):
        from app.layer_d.scoring import compute_overall_score
        scores = [90, 85, 80, 75, 70, 10, 5]  # last two should be excluded
        result = compute_overall_score(scores)
        assert result == round((90 + 85 + 80 + 75 + 70) / 5)

    def test_tier_labels(self):
        from app.layer_d.scoring import _tier
        assert _tier(80) == "Strong Engineering"
        assert _tier(60) == "Competent Engineering"
        assert _tier(40) == "Developing"
        assert _tier(0) == "Needs Work"


# ── router.py integration tests (mocked HTTP) ─────────────────────────────────

@pytest.fixture
def mock_github_repos():
    return [_make_repo("my-project"), _make_repo("another-repo")]


@pytest.fixture
def mock_healthy_raw():
    return {
        "name": "my-project",
        "full_name": "octocat/my-project",
        "fork": False,
        "archived": False,
        "size": 500,
        "default_branch": "main",
        "description": "A cool project",
        "pushed_at": "2024-03-15T10:00:00Z",
        "tree": HEALTHY_TREE,
        "commits": HEALTHY_COMMITS,
        "readme": HEALTHY_README,
        "tree_available": True,
        "commits_available": True,
    }


class TestRouterAnalysis:
    @pytest.mark.asyncio
    async def test_healthy_repo_scores_high(self, mock_github_repos, mock_healthy_raw):
        from app.layer_d.router import _analyze
        with patch("app.layer_d.github_client.fetch_user_repos",
                   new_callable=AsyncMock, return_value=mock_github_repos), \
             patch("app.layer_d.github_client.gather_repo_data",
                   new_callable=AsyncMock, return_value=mock_healthy_raw):
            result = await _analyze("octocat", "octocat")

        assert result["layer"] == "D"
        assert result["authenticity_score"] >= 60
        assert result["tier"] in ("Competent Engineering", "Strong Engineering")
        assert len(result["repos"]) > 0

    @pytest.mark.asyncio
    async def test_single_commit_repo_flagged(self, mock_github_repos):
        from app.layer_d.router import _analyze
        single_commit_raw = {
            "name": "my-project",
            "full_name": "octocat/my-project",
            "fork": False, "archived": False, "size": 200,
            "default_branch": "main", "description": "",
            "pushed_at": "2024-03-15T10:00:00Z",
            "tree": MINIMAL_TREE,
            "commits": SINGLE_COMMIT,
            "readme": None,
            "tree_available": True, "commits_available": True,
        }
        with patch("app.layer_d.github_client.fetch_user_repos",
                   new_callable=AsyncMock, return_value=mock_github_repos), \
             patch("app.layer_d.github_client.gather_repo_data",
                   new_callable=AsyncMock, return_value=single_commit_raw):
            result = await _analyze("octocat", "octocat")

        flag_ids = [f["id"] for f in result["global_flags"]]
        assert "instant_dump" in flag_ids

    @pytest.mark.asyncio
    async def test_all_forks_raises_422(self):
        from app.layer_d.router import _analyze
        import httpx
        from fastapi import HTTPException
        all_fork_repos = [_make_repo("fork1", fork=True), _make_repo("fork2", fork=True)]
        with patch("app.layer_d.github_client.fetch_user_repos",
                   new_callable=AsyncMock, return_value=all_fork_repos):
            with pytest.raises(HTTPException) as exc_info:
                await _analyze("octocat", "octocat")
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_user_raises_404(self):
        from app.layer_d.router import _analyze
        with patch("app.layer_d.github_client.fetch_user_repos",
                   new_callable=AsyncMock, return_value=[]):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await _analyze("nobody-xxxxxx-9999", "nobody")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_rate_limit_raises_429(self):
        from app.layer_d.router import _analyze
        with patch("app.layer_d.github_client.fetch_user_repos",
                   new_callable=AsyncMock,
                   side_effect=RuntimeError("GitHub rate-limit hit (429)")):
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await _analyze("octocat", "octocat")
        assert exc_info.value.status_code == 429
