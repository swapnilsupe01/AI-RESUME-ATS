"""
Layer D — File-presence & Commit-history Checks
================================================
All scoring functions return (score, status, detail) tuples where:
  score  — numeric contribution to repo total
  status — "present" | "partial" | "missing" | "unavailable"
  detail — short human-readable explanation
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# ── Regex helpers ─────────────────────────────────────────────────────────────
def _match_any(paths: List[str], patterns: List[str]) -> bool:
    for p in patterns:
        rx = re.compile(p, re.IGNORECASE)
        if any(rx.search(path) for path in paths):
            return True
    return False


# ── File-presence check definitions ──────────────────────────────────────────
# Each entry: (check_id, max_pts, patterns)
FILE_CHECKS: List[Tuple[str, int, List[str]]] = [
    ("tests",       15, [r"(?:^|/)tests?/", r"test_[^/]+\.py$", r"[^/]+_test\.py$",
                          r"[^/]+\.test\.(?:js|ts|jsx|tsx)$", r"[^/]+\.spec\.(?:js|ts)$",
                          r"__tests__/", r"spec/", r"src/test/"]),
    ("test_config",  5, [r"pytest\.ini$", r"conftest\.py$",
                          r"jest\.config\.[jt]s$", r"vitest\.config\.[jt]s$"]),
    ("e2e",          5, [r"cypress/", r"playwright\.config\.[jt]s$",
                          r"selenium", r"e2e/"]),
    ("docker",      10, [r"(?:^|/)Dockerfile(?:\.[^/]+)?$",
                          r"docker-compose\.ya?ml$", r"compose\.ya?ml$"]),
    ("ci_cd",       10, [r"\.github/workflows/[^/]+\.ya?ml$",
                          r"Jenkinsfile$", r"\.gitlab-ci\.ya?ml$",
                          r"\.circleci/config\.ya?ml$"]),
    ("readme",      10, [r"(?:^|/)readme(?:\..+)?$"]),
    ("deps",         5, [r"requirements(?:[^/]*)\.txt$", r"package\.json$",
                          r"pom\.xml$", r"pyproject\.toml$", r"build\.gradle(?:\.kts)?$",
                          r"go\.mod$", r"Cargo\.toml$"]),
    ("gitignore",    5, [r"(?:^|/)\.gitignore$"]),
    ("env_example",  5, [r"\.env\.(?:example|sample|template)$"]),
    ("license",      3, [r"(?:^|/)license(?:\..+)?$"]),
]

SECRET_PATTERNS = [r"(?:^|/)\.env$", r"\.pem$", r"id_rsa$", r"\.key$"]
TEMPLATE_ONLY_PATTERNS = [
    # Vite/CRA boilerplate markers
    r"src/App\.(jsx?|tsx?)$", r"src/main\.(jsx?|tsx?)$",
    r"public/index\.html$", r"src/index\.(js|ts|jsx|tsx)$",
]

LAZY_COMMIT_RX = re.compile(
    r"^(?:initial commit|update|done|test|fix|changes|work|wip|commit|add|misc|"
    r"temp|final|edit|upload(?:ed)?|first commit|push|hello|ok|checkpoint|"
    r"asdf|qwerty|aaa+|xxx+|\.\.\.|no message)[\s.!]*$",
    re.IGNORECASE,
)

INTENT_RX: Dict[str, re.Pattern] = {
    "feat":     re.compile(r"^feat(?:\(.+\))?:", re.I),
    "fix":      re.compile(r"^fix(?:\(.+\))?:", re.I),
    "docs":     re.compile(r"^docs?(?:\(.+\))?:", re.I),
    "test":     re.compile(r"^tests?(?:\(.+\))?:", re.I),
    "chore":    re.compile(r"^chore(?:\(.+\))?:", re.I),
    "refactor": re.compile(r"^refactor(?:\(.+\))?:", re.I),
    "style":    re.compile(r"^style(?:\(.+\))?:", re.I),
    "ci":       re.compile(r"^ci(?:\(.+\))?:", re.I),
    "build":    re.compile(r"^build(?:\(.+\))?:", re.I),
    "perf":     re.compile(r"^perf(?:\(.+\))?:", re.I),
}


# ── File-presence checks ──────────────────────────────────────────────────────

def run_file_checks(tree: List[str], readme_text: Optional[str]) -> Dict[str, Any]:
    """
    Run all file-presence checks against *tree* (list of blob paths).
    Returns {check_id: {"score": int, "status": str, "detail": str}}.
    """
    results: Dict[str, Any] = {}

    for (cid, max_pts, patterns) in FILE_CHECKS:
        present = _match_any(tree, patterns)

        # Bonus logic for README quality
        if cid == "readme" and present:
            if readme_text:
                word_count = len(readme_text.split())
                has_setup = bool(re.search(r"(?:install|setup|getting started|usage|run)", readme_text, re.I))
                if word_count >= 300 and has_setup:
                    status, score, detail = "present", max_pts, f"README with {word_count} words and setup section."
                elif word_count >= 100:
                    status, score, detail = "partial", max_pts // 2, f"README exists ({word_count} words) but lacks setup section."
                else:
                    status, score, detail = "partial", max_pts // 3, f"README is very short ({word_count} words)."
            else:
                status, score, detail = "partial", max_pts // 3, "README exists in tree but content was not provided or is empty."
        elif present:
            status, score, detail = "present", max_pts, f"Found in repository."
        else:
            status, score, detail = "missing", 0, f"Not detected in file tree."

        results[cid] = {"score": score, "max": max_pts, "status": status, "detail": detail}

    # Committed-secrets penalty
    has_secrets = _match_any(tree, SECRET_PATTERNS)
    results["secrets"] = {
        "score": -10 if has_secrets else 0,
        "max": 0,
        "status": "fail" if has_secrets else "pass",
        "detail": "⚠️ Sensitive file (.env/pem/key) committed!" if has_secrets else "No secrets detected.",
    }

    # Template-only detection (bonus deduction)
    template_hits = sum(1 for _, _, pats in FILE_CHECKS[:3] for _ in [None]
                        if _match_any(tree, TEMPLATE_ONLY_PATTERNS))
    meaningful = sum(1 for v in results.values() if v["status"] == "present")
    is_template_only = (template_hits > 0 and meaningful <= 2 and len(tree) < 20)
    results["template_only"] = {
        "score": -5 if is_template_only else 0,
        "max": 0,
        "status": "warn" if is_template_only else "pass",
        "detail": "Repo appears to be an unmodified scaffold/template." if is_template_only else "Not a bare template.",
    }

    return results


# ── Commit-history checks ─────────────────────────────────────────────────────

def _parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify_message(msg: str) -> str:
    """Return intent label for a commit message."""
    msg = msg.strip().splitlines()[0]  # first line only
    for intent, rx in INTENT_RX.items():
        if rx.match(msg):
            return intent
    if LAZY_COMMIT_RX.match(msg):
        return "lazy"
    return "unknown"


def run_commit_checks(commits: List[Dict], candidate_login: Optional[str]) -> Dict[str, Any]:
    """
    Analyse commit list and return per-dimension scores.
    Returns {dim_id: {"score": int, "max": int, "status": str, "detail": str, ...}}.
    """
    n = len(commits)
    results: Dict[str, Any] = {}

    # ── D2a Commit count ──────────────────────────────────────────────────────
    if n == 0:
        results["commit_count"] = {"score": 0, "max": 10, "status": "missing",
                                    "detail": "No commits found."}
    elif n == 1:
        results["commit_count"] = {"score": 0, "max": 10, "status": "fail",
                                    "detail": "Only 1 commit — Instant Dump Risk.",
                                    "flag": "instant_dump"}
    elif n < 5:
        results["commit_count"] = {"score": 4, "max": 10, "status": "partial",
                                    "detail": f"{n} commits — sparse history."}
    elif n < 8:
        results["commit_count"] = {"score": 7, "max": 10, "status": "partial",
                                    "detail": f"{n} commits — developing history."}
    else:
        results["commit_count"] = {"score": 10, "max": 10, "status": "present",
                                    "detail": f"{n} commits — good development history."}

    # ── D2b Time span ─────────────────────────────────────────────────────────
    dates = []
    for c in commits:
        d = _parse_date(
            (c.get("commit", {}).get("author") or {}).get("date")
        )
        if d:
            dates.append(d)

    if len(dates) >= 2:
        span = (max(dates) - min(dates)).days
    else:
        span = 0

    if span >= 30:
        results["time_span"] = {"score": 5, "max": 5, "status": "present",
                                  "detail": f"{span} days of active development."}
    elif span >= 7:
        results["time_span"] = {"score": 3, "max": 5, "status": "partial",
                                  "detail": f"{span} days span — short but nonzero."}
    else:
        results["time_span"] = {"score": 0, "max": 5, "status": "missing",
                                  "detail": f"Span ≤ {span} days — no meaningful development window."}

    # ── D3 Message quality ────────────────────────────────────────────────────
    intent_counts: Dict[str, int] = {}
    for c in commits:
        msg = (c.get("commit", {}).get("message") or "").strip()
        intent = classify_message(msg)
        intent_counts[intent] = intent_counts.get(intent, 0) + 1

    lazy = intent_counts.get("lazy", 0) + intent_counts.get("unknown", 0)
    descriptive = n - lazy
    quality_ratio = descriptive / n if n > 0 else 0.0
    lazy_ratio = lazy / n if n > 0 else 0.0

    if quality_ratio >= 0.7:
        msg_score, msg_status = 7, "present"
        msg_detail = f"{int(quality_ratio*100)}% descriptive commit messages."
    elif quality_ratio >= 0.4:
        msg_score, msg_status = 4, "partial"
        msg_detail = f"{int(quality_ratio*100)}% descriptive messages — room to improve."
    else:
        msg_score, msg_status = 1, "missing"
        msg_detail = f"Only {int(quality_ratio*100)}% descriptive — mostly lazy/unknown messages."

    results["message_quality"] = {
        "score": msg_score, "max": 7, "status": msg_status,
        "detail": msg_detail,
        "intent_counts": intent_counts,
        "flag": "generic_commit_messages" if lazy_ratio > 0.5 else None,
    }

    # ── D2c Author match ──────────────────────────────────────────────────────
    if candidate_login:
        authored = 0
        for c in commits:
            author = c.get("author") or {}
            login = author.get("login", "")
            co_author = (c.get("commit", {}).get("author") or {}).get("name", "")
            if login.lower() == candidate_login.lower() or \
               candidate_login.lower() in co_author.lower():
                authored += 1
        ratio = authored / n if n > 0 else 0.0
        if ratio >= 0.8:
            results["author_match"] = {"score": 5, "max": 5, "status": "present",
                                        "detail": f"{int(ratio*100)}% commits authored by candidate."}
        elif ratio >= 0.4:
            results["author_match"] = {"score": 3, "max": 5, "status": "partial",
                                        "detail": f"{int(ratio*100)}% commits authored by candidate."}
        else:
            results["author_match"] = {"score": 0, "max": 5, "status": "missing",
                                        "detail": f"Only {int(ratio*100)}% commits by candidate."}
    else:
        results["author_match"] = {"score": 3, "max": 5, "status": "unavailable",
                                    "detail": "Author login not available for comparison."}

    return results, intent_counts


# ── Test-to-source ratio ──────────────────────────────────────────────────────

def test_to_source_ratio(tree: List[str]) -> Tuple[float, str]:
    """Return (ratio, status) based on test vs source file counts."""
    test_rx = re.compile(r"(?:^|/)(?:tests?/|__tests__/|spec/)|test_[^/]+\.py$|[^/]+\.(?:test|spec)\.[jt]sx?$", re.I)
    src_rx = re.compile(r"\.[pj][yst][x]?$|\.java$|\.go$|\.rb$|\.rs$|\.cs$", re.I)
    tests = sum(1 for p in tree if test_rx.search(p))
    sources = sum(1 for p in tree if src_rx.search(p))
    if sources == 0:
        return 0.0, "unavailable"
    ratio = tests / sources
    if ratio >= 0.15:
        return ratio, "present"
    elif ratio > 0:
        return ratio, "partial"
    return ratio, "missing"
