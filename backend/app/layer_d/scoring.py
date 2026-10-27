"""
Layer D — Scoring Engine
=========================
Converts raw check results into per-repo and overall authenticity scores.
Emits global flags and fix suggestions.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# ── Tier labels ───────────────────────────────────────────────────────────────
def _tier(score: float) -> str:
    if score >= 80: return "Strong Engineering"
    if score >= 60: return "Competent Engineering"
    if score >= 40: return "Developing"
    return "Needs Work"


# ── Fix suggestion catalogue ──────────────────────────────────────────────────
FIXES: Dict[str, str] = {
    "tests":         "Add a tests/ folder with pytest (Python) or Jest (JS) unit tests covering your core logic.",
    "test_config":   "Add a pytest.ini or jest.config.js to configure your test runner.",
    "e2e":           "Add Cypress or Playwright end-to-end tests to demonstrate full-stack coverage.",
    "docker":        "Add a Dockerfile and docker-compose.yml to show production deployment readiness.",
    "ci_cd":         "Add a .github/workflows/ci.yml that installs deps and runs your tests automatically.",
    "readme":        "Expand your README to include a project description, installation steps, and usage examples (aim for 300+ words).",
    "deps":          "Add a requirements.txt (Python) or package.json (Node) dependency file to your project root.",
    "gitignore":     "Add a .gitignore file to exclude build artifacts, venv/, node_modules/, and .env files.",
    "env_example":   "Add a .env.example file listing required environment variables (never commit real secrets).",
    "license":       "Add an open-source LICENSE file (MIT or Apache-2.0 are good choices).",
    "secrets":       "Remove sensitive files (.env, .pem, keys) from git history using 'git filter-branch' or BFG Cleaner.",
    "template_only": "Customise beyond the scaffold: add real business logic, tests, and documentation.",
    "instant_dump":  "Commit small and often throughout development; use feat:/fix:/docs: prefixed messages.",
    "generic_commit_messages": "Use Conventional Commits (feat:, fix:, docs:, test:, chore:) for meaningful commit messages.",
    "time_span":     "Start committing your work early and regularly — recruiters look for consistent development history.",
    "author_match":  "Ensure your GitHub login matches the author field in your commits.",
    "missing_tests": "Add a tests/ folder with at least basic unit tests.",
    "missing_docker": "Add a Dockerfile to containerize your application.",
    "non_forked":    None,  # positive flag — no fix needed
}


# ── Per-repo score ────────────────────────────────────────────────────────────

def compute_repo_score(file_checks: Dict[str, Any], commit_checks: Dict[str, Any]) -> Tuple[int, Dict]:
    """
    Sum all check scores, normalise to 0–100.
    Returns (normalised_score, raw totals dict).
    """
    total = 0
    max_pts = 0
    for checks in (file_checks, commit_checks):
        for v in checks.values():
            total += v.get("score", 0)
            max_pts += max(v.get("max", 0), 0)

    if max_pts == 0:
        return 50, {"total": 0, "max": 0}

    # Floor at 0 (secrets can push negative)
    raw = max(total, 0)
    score = round((raw / max_pts) * 100)
    return min(score, 100), {"total": raw, "max": max_pts}


# ── Global flags ──────────────────────────────────────────────────────────────

def compute_global_flags(repos_data: List[Dict[str, Any]], all_repo_infos: List[Dict]) -> List[Dict]:
    """
    Aggregate per-repo check results into high-level global flags.
    """
    flags: List[Dict] = []

    # Non-forked flag
    fork_count = sum(1 for r in all_repo_infos if r.get("fork"))
    total = len(all_repo_infos)
    if total > 0 and fork_count / total < 0.5:
        flags.append({
            "id": "non_forked",
            "status": "pass",
            "message": "Non-Forked: most repositories built from scratch.",
        })
    else:
        flags.append({
            "id": "non_forked",
            "status": "warn",
            "message": f"{fork_count}/{total} repos are forks — original work not demonstrated.",
            "fix": "Create original projects rather than forking templates.",
        })

    # Scan all repos for recurring issues
    has_instant_dump = False
    has_generic_msgs = False
    missing_tests = True
    missing_docker = True
    has_secrets = False

    for rd in repos_data:
        fc = rd.get("file_checks", {})
        cc = rd.get("commit_checks", {})
        if cc.get("commit_count", {}).get("flag") == "instant_dump":
            has_instant_dump = True
        if cc.get("message_quality", {}).get("flag") == "generic_commit_messages":
            has_generic_msgs = True
        if fc.get("tests", {}).get("status") == "present":
            missing_tests = False
        if fc.get("docker", {}).get("status") == "present":
            missing_docker = False
        if fc.get("secrets", {}).get("status") == "fail":
            has_secrets = True

    if has_instant_dump:
        flags.append({
            "id": "instant_dump",
            "status": "fail",
            "message": "One or more repos have only 1 commit — no development history.",
            "fix": FIXES["instant_dump"],
        })

    if has_generic_msgs:
        flags.append({
            "id": "generic_commit_messages",
            "status": "warn",
            "message": "Over 50% of commits have generic, uninformative messages.",
            "fix": FIXES["generic_commit_messages"],
        })

    if missing_tests:
        flags.append({
            "id": "missing_tests",
            "status": "warn",
            "message": "No unit test suite found in any scanned repository.",
            "fix": FIXES["tests"],
        })

    if missing_docker:
        flags.append({
            "id": "missing_docker",
            "status": "warn",
            "message": "No Docker containerization found in any repository.",
            "fix": FIXES["docker"],
        })

    if has_secrets:
        flags.append({
            "id": "committed_secrets",
            "status": "fail",
            "message": "Sensitive files (.env / .pem / keys) detected in a repository tree.",
            "fix": FIXES["secrets"],
        })

    return flags


# ── Overall authenticity score ────────────────────────────────────────────────

def compute_overall_score(repo_scores: List[int]) -> int:
    """
    Average the best 5 repo scores (or all if fewer than 5).
    This prevents a single old/tiny repo from dragging down the result.
    """
    if not repo_scores:
        return 0
    top = sorted(repo_scores, reverse=True)[:5]
    return round(sum(top) / len(top))


# ── Flag enrichment for per-repo checks ──────────────────────────────────────

def build_repo_flags(file_checks: Dict, commit_checks: Dict) -> List[Dict]:
    """Return a list of per-repo flag dicts (status warn/fail) with fix strings."""
    flags = []
    for check_id, data in {**file_checks, **commit_checks}.items():
        status = data.get("status", "")
        if status in ("missing", "fail", "partial", "warn"):
            flag = {
                "id": check_id,
                "status": "fail" if status in ("missing", "fail") else "warn",
                "message": data.get("detail", ""),
            }
            fix = FIXES.get(check_id)
            if fix:
                flag["fix"] = fix
            flags.append(flag)
    return flags
