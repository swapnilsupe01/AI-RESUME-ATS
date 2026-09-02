"""
Layer D — Code Quality & Authenticity Analyzer (Anti-Fork / Anti-Template).

Solves the critical recruiter blindspot: A candidate may own their GitHub account (passes Layer C),
but their linked repositories could be:
  1. Forked from someone else's original project.
  2. "ZIP-dumped" — a downloaded tutorial pushed in a single commit with no actual dev history.
  3. Cloned/copied from popular YouTube / Coursera template repos.
  4. Lacking any real engineering practices (no tests, no CI/CD, no Docker).

This module audits each linked repository across 5 independent forensic dimensions:

  Dimension 1 — Fork & Upstream Origin Check     (25%): Was this repo forked or is it original?
  Dimension 2 — Commit Timeline Cadence          (25%): Organic multi-week dev vs instant ZIP-dump?
  Dimension 3 — Commit Message Semantic Quality  (15%): Professional git tags vs generic "update"?
  Dimension 4 — Tutorial & Boilerplate Scanner   (20%): Known tutorial fingerprints detected?
  Dimension 5 — Production Engineering Standards (15%): Tests, Docker, CI/CD present?

Additionally provides:
  - Per-year GitHub Contribution Graph data (commits by year + per repo breakdown)
  - Isolation Forest anomaly detection on commit temporal patterns
  - NER-style commit message intent classification (feat / fix / refactor / docs / chore)
"""

import re
import math
from typing import Dict, Any, List, Optional, Tuple
import httpx
from datetime import datetime, timezone


# ── Constants ──────────────────────────────────────────────────────────────────

TUTORIAL_FINGERPRINT_PATTERNS = [
    r'youtube', r'tutorial', r'crash.?course', r'udemy', r'coursera',
    r'freecodecamp', r'clone', r'todo.?app', r'hello.?world', r'starter.?kit',
    r'boilerplate', r'template', r'step.?1', r'follow.?along', r'assignment',
    r'homework', r'exercise', r'practice', r'learning.?project', r'beginner',
    r'workshop', r'hands.?on', r'getting.?started', r'intro.?to', r'basic.?app',
]

PROFESSIONAL_COMMIT_TAGS = re.compile(
    r'\b(feat|fix|refactor|docs|chore|test|style|build|ci|perf|revert|hotfix|release|breaking)\b',
    re.IGNORECASE
)

LAZY_COMMIT_PATTERNS = re.compile(
    r'^(initial commit|update|done|test|fix|changes|work|wip|commit|add|misc|temp|final|edit|uploaded?|first commit|push|hello|ok|checkpoint)[\s.!]*$',
    re.IGNORECASE
)

PRODUCTION_SIGNALS = {
    "tests": [r'tests?/', r'test_.*\.py', r'__tests__', r'spec\.js', r'\.spec\.ts', r'pytest', r'jest', r'unittest'],
    "docker": [r'dockerfile', r'docker-compose\.ya?ml'],
    "ci_cd": [r'\.github/workflows/', r'jenkinsfile', r'\.circleci/', r'gitlab-ci\.yml', r'\.travis\.yml', r'bitbucket-pipelines'],
    "linting": [r'\.eslintrc', r'\.flake8', r'pylintrc', r'\.prettierrc', r'pre-commit'],
}

QUALITY_TIERS = {
    "production": {"min": 80, "label": "Production-Ready Original", "color": "green", "icon": "🟢"},
    "competent":  {"min": 55, "label": "Competent Engineering",      "color": "yellow","icon": "🟡"},
    "basic":      {"min": 35, "label": "Basic / Unstructured",       "color": "orange","icon": "🟠"},
    "tutorial":   {"min": 0,  "label": "Suspected Tutorial / Template / Fork", "color": "red", "icon": "🔴"},
}

# Mock commit timeline data for offline demonstration (swapnilsupe01)
MOCK_COMMIT_GRAPH: Dict[str, Any] = {
    "swapnilsupe01/ai-resume-ats": {
        "total_commits": 48,
        "commit_span_days": 74,
        "first_commit_date": "2024-01-10",
        "latest_commit_date": "2024-03-25",
        "is_fork": False,
        "parent_repo": None,
        "sample_messages": [
            "feat: integrate Sentence-BERT tokenizer and vector cache",
            "fix: handle edge case in LinkedIn URL regex parser",
            "refactor: Docker multi-stage build optimization",
            "ci: add GitHub Actions pipeline for linting and tests",
            "feat: add 10-signal identity fraud detection engine",
            "docs: update README with triple-layer architecture",
            "test: add pytest coverage for evidence scorer",
            "perf: async httpx client connection pooling",
        ],
        "tree_signals": {
            "tests": True,
            "docker": True,
            "ci_cd": True,
            "linting": True,
        },
        "yearly_commits": {
            "2024": 48
        }
    },
    "swapnilsupe01/smart-hospital": {
        "total_commits": 23,
        "commit_span_days": 31,
        "first_commit_date": "2024-02-01",
        "latest_commit_date": "2024-03-03",
        "is_fork": False,
        "parent_repo": None,
        "sample_messages": [
            "feat: FastAPI REST endpoints for patient management",
            "fix: SQLAlchemy session handling issue",
            "refactor: split routes into blueprints",
            "chore: update docker-compose for dev environment",
            "feat: React dashboard for appointment booking",
        ],
        "tree_signals": {
            "tests": False,
            "docker": True,
            "ci_cd": False,
            "linting": False,
        },
        "yearly_commits": {
            "2024": 23
        }
    }
}


# ── Isolation Forest (lightweight implementation) ──────────────────────────────

def _isolation_forest_anomaly_score(commit_intervals_days: List[float]) -> float:
    """
    Lightweight Isolation Forest-inspired anomaly scoring for commit cadence.
    
    Real Isolation Forest (sklearn) isolates anomalies by randomly partitioning
    feature space. Here we approximate the key insight:
    - A burst pattern (all commits in < 1 day) = anomaly score close to 1.0 (very anomalous).
    - Organic spread pattern (commits over weeks) = anomaly score close to 0.0 (normal).
    
    Returns anomaly_score in [0, 1] where:
      < 0.3 = organic developer pattern
      0.3–0.6 = borderline
      > 0.6 = suspicious burst / dump pattern
    """
    if not commit_intervals_days:
        return 0.5  # Unknown
    
    if len(commit_intervals_days) == 1:
        # Single commit or single interval = maximum anomaly
        return 1.0

    mean_interval = sum(commit_intervals_days) / len(commit_intervals_days)
    variance = sum((x - mean_interval) ** 2 for x in commit_intervals_days) / len(commit_intervals_days)
    std_dev = math.sqrt(variance) if variance > 0 else 0

    # High variance + near-zero mean = burst pattern (dump)
    if mean_interval < 0.1:  # Less than 2.4 hours average between commits
        return 0.85

    # Low mean interval (< 1 day) with low std_dev = suspiciously uniform burst
    if mean_interval < 1.0 and std_dev < 0.5:
        return 0.70

    # Healthy: commits spread over days/weeks
    normalized_spread = min(1.0, mean_interval / 14.0)  # 14 days = ideal spread
    return max(0.0, 1.0 - normalized_spread)


# ── Commit Message NER / Intent Classifier ─────────────────────────────────────

def _classify_commit_intent(message: str) -> str:
    """
    NER-style token classifier for commit message intent.
    Maps a commit message to one of: feat | fix | refactor | docs | test | chore | lazy
    Uses regex-based token scanning similar to NER rule-based pipelines.
    """
    msg_lower = message.strip().lower()
    
    if LAZY_COMMIT_PATTERNS.match(msg_lower):
        return "lazy"
    
    tag_match = PROFESSIONAL_COMMIT_TAGS.search(message)
    if tag_match:
        tag = tag_match.group(1).lower()
        # Normalize aliases
        if tag in ("hotfix", "fix", "revert"):
            return "fix"
        if tag in ("build", "ci", "chore"):
            return "chore"
        if tag in ("docs",):
            return "docs"
        if tag in ("test",):
            return "test"
        if tag in ("perf", "style", "refactor"):
            return "refactor"
        if tag in ("feat", "feature", "release", "breaking"):
            return "feat"
        return tag
    
    # Heuristic keyword scan (NLP pattern matching)
    if any(w in msg_lower for w in ("add", "implement", "create", "integrate", "build", "new")):
        return "feat"
    if any(w in msg_lower for w in ("fix", "bug", "error", "resolve", "patch", "handle")):
        return "fix"
    if any(w in msg_lower for w in ("refactor", "clean", "optimize", "improve", "restructure")):
        return "refactor"
    if any(w in msg_lower for w in ("doc", "readme", "comment", "document")):
        return "docs"
    if any(w in msg_lower for w in ("test", "spec", "assert", "coverage")):
        return "test"
    
    return "unknown"


def _score_commit_messages(messages: List[str]) -> Tuple[float, Dict[str, int]]:
    """
    Score the quality of a set of commit messages.
    Returns (score_0_100, intent_distribution_dict).
    """
    if not messages:
        return 30.0, {}

    intent_counts: Dict[str, int] = {}
    professional_count = 0
    lazy_count = 0

    for msg in messages:
        intent = _classify_commit_intent(msg)
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        if intent == "lazy" or intent == "unknown":
            lazy_count += 1
        else:
            professional_count += 1

    total = len(messages)
    professional_ratio = professional_count / total if total > 0 else 0

    # Score: professional ratio + length bonus
    avg_length = sum(len(m) for m in messages) / total
    length_bonus = min(20, avg_length / 4)  # Up to 20 pts for descriptive messages

    score = (professional_ratio * 80) + length_bonus
    return round(min(100.0, score), 1), intent_counts


# ── Per-Dimension Scoring Functions ───────────────────────────────────────────

def _score_fork_origin(repo_meta: Dict[str, Any]) -> Tuple[float, str]:
    """Dimension 1: Fork & Upstream Origin."""
    is_fork = repo_meta.get("is_fork", False)
    parent = repo_meta.get("parent_repo")

    if is_fork and parent:
        return 10.0, f"Repository is a fork of '{parent}'. This may be derivative work rather than original engineering."
    if is_fork:
        return 20.0, "Repository appears to be forked. No parent detected, but fork flag is set."
    return 100.0, "Non-forked: Repository was built from scratch (original root commit)."


def _score_commit_cadence(repo_meta: Dict[str, Any]) -> Tuple[float, str, float]:
    """Dimension 2: Commit Timeline & Organic Cadence."""
    total_commits = repo_meta.get("total_commits", 1)
    span_days = repo_meta.get("commit_span_days", 0)

    if total_commits <= 1:
        anomaly = 1.0
        return 5.0, "Single commit: Entire codebase was pushed in one commit. Likely a ZIP-dump from a downloaded tutorial.", anomaly

    if span_days <= 0:
        span_days = 0.5

    commits_per_day = total_commits / span_days

    # Simulate commit intervals for Isolation Forest
    # In production: use actual commit timestamps from API
    if total_commits > 1:
        avg_interval = span_days / (total_commits - 1)
        # Generate synthetic intervals for anomaly scoring
        intervals = [avg_interval] * (total_commits - 1)
    else:
        intervals = [0.0]

    anomaly_score = _isolation_forest_anomaly_score(intervals)

    if span_days < 1 and total_commits > 5:
        score = 15.0
        explanation = f"Burst dump detected: {total_commits} commits in under 1 day (Anomaly Score: {anomaly_score:.2f})."
    elif span_days <= 3 and total_commits <= 3:
        score = 25.0
        explanation = f"Minimal activity: Only {total_commits} commits over {span_days} days."
    elif span_days >= 14 and total_commits >= 10:
        score = 95.0
        explanation = f"Organic growth: {total_commits} commits across {span_days} days (healthy development cadence)."
    elif span_days >= 7:
        score = 75.0
        explanation = f"Moderate activity: {total_commits} commits over {span_days} days."
    else:
        score = 50.0
        explanation = f"Limited history: {total_commits} commits over {span_days} days."

    return score, explanation, anomaly_score


def _score_tutorial_fingerprint(repo_meta: Dict[str, Any]) -> Tuple[float, str]:
    """Dimension 4: Tutorial & Boilerplate Fingerprint Scanner."""
    scan_text = " ".join([
        repo_meta.get("repo_name", ""),
        repo_meta.get("description", ""),
        repo_meta.get("readme_preview", ""),
        " ".join(repo_meta.get("topics", [])),
    ]).lower()

    matched_patterns = []
    for pattern in TUTORIAL_FINGERPRINT_PATTERNS:
        if re.search(pattern, scan_text, re.IGNORECASE):
            matched_patterns.append(pattern.replace(r'\b', '').replace(r'.?', ' ').strip())

    if not matched_patterns:
        return 100.0, "No tutorial, boilerplate, or template fingerprints detected in repo name, description, topics, or README."
    
    if len(matched_patterns) >= 3:
        return 10.0, f"Strong tutorial markers detected: '{', '.join(matched_patterns[:3])}'. High probability of copied course project."
    
    return 50.0, f"Possible template markers: '{', '.join(matched_patterns)}'. Manual review recommended."


def _score_production_standards(tree_signals: Dict[str, bool]) -> Tuple[float, List[str], List[str]]:
    """Dimension 5: Production Engineering Standards."""
    passing = []
    failing = []
    score = 0.0
    weights = {"tests": 35, "docker": 25, "ci_cd": 30, "linting": 10}

    for signal, present in tree_signals.items():
        w = weights.get(signal, 10)
        label_map = {
            "tests": "Unit Test Suite (pytest/jest)",
            "docker": "Docker Containerization",
            "ci_cd": "CI/CD Pipeline (.github/workflows or Jenkinsfile)",
            "linting": "Code Quality / Linting Config",
        }
        label = label_map.get(signal, signal)
        if present:
            score += w
            passing.append(label)
        else:
            failing.append(label)

    return round(score, 1), passing, failing


# ── Yearly Contribution Graph Builder ─────────────────────────────────────────

def build_contribution_graph(all_repo_audits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a GitHub-style contribution graph from all audited repositories.
    Aggregates commits per year per repo for the frontend interactive chart.
    
    Returns:
    {
      "yearly_totals": {"2022": 10, "2023": 35, "2024": 48},
      "per_repo_by_year": {
        "2024": [
          {"repo": "swapnilsupe01/ai-resume-ats", "commits": 48},
          {"repo": "swapnilsupe01/smart-hospital", "commits": 23}
        ]
      },
      "total_tracked_commits": 119,
      "years_active": ["2022", "2023", "2024"]
    }
    """
    yearly_totals: Dict[str, int] = {}
    per_repo_by_year: Dict[str, List[Dict[str, Any]]] = {}

    for audit in all_repo_audits:
        repo_full = audit.get("repo_full_name", "unknown/repo")
        yearly = audit.get("yearly_commits", {})
        
        for year, count in yearly.items():
            yearly_totals[year] = yearly_totals.get(year, 0) + count
            if year not in per_repo_by_year:
                per_repo_by_year[year] = []
            per_repo_by_year[year].append({
                "repo": repo_full,
                "commits": count,
                "quality_tier": audit.get("quality_tier", "unknown"),
                "authenticity_score": audit.get("authenticity_score", 0),
            })

    # Sort years
    sorted_years = sorted(yearly_totals.keys())

    return {
        "yearly_totals": {y: yearly_totals[y] for y in sorted_years},
        "per_repo_by_year": per_repo_by_year,
        "total_tracked_commits": sum(yearly_totals.values()),
        "years_active": sorted_years,
    }


# ── Live GitHub Commit Fetch ───────────────────────────────────────────────────

async def _fetch_repo_commit_metadata(owner: str, repo: str) -> Dict[str, Any]:
    """
    Fetch commit count, timeline, fork status, and production signals from GitHub API.
    Falls back to mock data for offline demo.
    """
    mock_key = f"{owner}/{repo}".lower()
    mock_data = MOCK_COMMIT_GRAPH.get(mock_key)

    headers = {
        "User-Agent": "AI-Resume-ATS-CodeQualityAnalyzer",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # 1. Repository metadata (fork, parent)
            repo_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
            if repo_res.status_code != 200:
                raise ValueError(f"Repo API returned {repo_res.status_code}")
            repo_data = repo_res.json()

            is_fork = repo_data.get("fork", False)
            parent_repo = None
            if is_fork and "parent" in repo_data:
                parent_repo = repo_data["parent"].get("full_name")

            # 2. Commits (last 100)
            commits_res = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100",
                headers=headers
            )
            commits = commits_res.json() if commits_res.status_code == 200 else []
            total_commits = len(commits)

            # Parse commit dates for timeline analysis
            commit_dates = []
            yearly_commits: Dict[str, int] = {}
            sample_messages: List[str] = []

            for c in commits:
                try:
                    date_str = c.get("commit", {}).get("author", {}).get("date", "")
                    if date_str:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        commit_dates.append(dt)
                        year = str(dt.year)
                        yearly_commits[year] = yearly_commits.get(year, 0) + 1
                    msg = c.get("commit", {}).get("message", "").split("\n")[0][:120]
                    if msg:
                        sample_messages.append(msg)
                except Exception:
                    pass

            sample_messages = sample_messages[:15]

            # Commit span in days
            span_days = 0
            if len(commit_dates) >= 2:
                oldest = min(commit_dates)
                newest = max(commit_dates)
                span_days = (newest - oldest).days

            first_commit = min(commit_dates).strftime("%Y-%m-%d") if commit_dates else "Unknown"
            latest_commit = max(commit_dates).strftime("%Y-%m-%d") if commit_dates else "Unknown"

            # 3. Repository tree — check for production signals
            tree_res = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1",
                headers=headers
            )
            tree_files: List[str] = []
            if tree_res.status_code == 200:
                tree_files = [item.get("path", "").lower() for item in tree_res.json().get("tree", [])]

            tree_signals: Dict[str, bool] = {}
            for sig_name, sig_patterns in PRODUCTION_SIGNALS.items():
                matched = any(
                    any(re.search(p, f, re.IGNORECASE) for p in sig_patterns)
                    for f in tree_files
                )
                tree_signals[sig_name] = matched

            return {
                "is_fork": is_fork,
                "parent_repo": parent_repo,
                "total_commits": total_commits,
                "commit_span_days": span_days,
                "first_commit_date": first_commit,
                "latest_commit_date": latest_commit,
                "sample_messages": sample_messages,
                "tree_signals": tree_signals,
                "yearly_commits": yearly_commits,
                "live_retrieved": True,
            }

    except Exception as e:
        print(f"[Layer D Notice]: Live commit fetch for {owner}/{repo} failed ({e}). Using cached profile.")

    if mock_data:
        return {**mock_data, "live_retrieved": False}

    # Generic fallback for unknown repos
    return {
        "is_fork": False,
        "parent_repo": None,
        "total_commits": 5,
        "commit_span_days": 2,
        "first_commit_date": "Unknown",
        "latest_commit_date": "Unknown",
        "sample_messages": ["initial commit", "update", "done"],
        "tree_signals": {"tests": False, "docker": False, "ci_cd": False, "linting": False},
        "yearly_commits": {},
        "live_retrieved": False,
    }


# ── Main Entry Point ───────────────────────────────────────────────────────────

async def audit_repository_authenticity(
    owner: str,
    repo: str,
    repo_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the 5-dimension code quality & authenticity forensic audit on a repository.
    """
    commit_meta = await _fetch_repo_commit_metadata(owner, repo)

    # ── Dimension 1: Fork & Upstream Origin ───────────────────────────────────
    d1_score, d1_explanation = _score_fork_origin(commit_meta)

    # ── Dimension 2: Commit Timeline Cadence ──────────────────────────────────
    d2_score, d2_explanation, anomaly_score = _score_commit_cadence(commit_meta)

    # ── Dimension 3: Commit Message Semantic Quality ──────────────────────────
    d3_score, intent_distribution = _score_commit_messages(commit_meta.get("sample_messages", []))

    msg_count = len(commit_meta.get("sample_messages", []))
    professional_msgs = sum(v for k, v in intent_distribution.items() if k not in ("lazy", "unknown"))
    d3_explanation = (
        f"Analyzed {msg_count} commit messages. "
        f"Intent distribution: {intent_distribution}. "
        f"{professional_msgs} professional semantic tags detected."
    )

    # ── Dimension 4: Tutorial / Boilerplate Fingerprint ───────────────────────
    scan_meta = {
        "repo_name": repo,
        "description": (repo_metadata or {}).get("description", ""),
        "readme_preview": (repo_metadata or {}).get("readme_preview", ""),
        "topics": (repo_metadata or {}).get("topics", []),
    }
    d4_score, d4_explanation = _score_tutorial_fingerprint(scan_meta)

    # ── Dimension 5: Production Engineering Rigor ─────────────────────────────
    d5_score, d5_passing, d5_failing = _score_production_standards(commit_meta.get("tree_signals", {}))

    d5_explanation = ""
    if d5_passing:
        d5_explanation += f"✅ Present: {', '.join(d5_passing)}. "
    if d5_failing:
        d5_explanation += f"❌ Missing: {', '.join(d5_failing)}."

    # ── Weighted Authenticity Score ────────────────────────────────────────────
    WEIGHTS = {
        "fork_origin":       0.25,
        "commit_cadence":    0.25,
        "commit_quality":    0.15,
        "tutorial_scan":     0.20,
        "prod_standards":    0.15,
    }

    authenticity_score = round(
        d1_score * WEIGHTS["fork_origin"] +
        d2_score * WEIGHTS["commit_cadence"] +
        d3_score * WEIGHTS["commit_quality"] +
        d4_score * WEIGHTS["tutorial_scan"] +
        d5_score * WEIGHTS["prod_standards"],
        1
    )

    # ── Quality Tier Classification ────────────────────────────────────────────
    if authenticity_score >= 80:
        tier_key = "production"
    elif authenticity_score >= 55:
        tier_key = "competent"
    elif authenticity_score >= 35:
        tier_key = "basic"
    else:
        tier_key = "tutorial"

    tier = QUALITY_TIERS[tier_key]

    # ── Audit Highlights ───────────────────────────────────────────────────────
    highlights = []
    
    # Fork status
    if not commit_meta.get("is_fork", False):
        highlights.append({"status": "pass", "text": "Non-Forked: Built from scratch (original root commit)"})
    else:
        highlights.append({"status": "fail", "text": f"Fork Detected: Derived from '{commit_meta.get('parent_repo', 'unknown parent')}'"})

    # Timeline
    commits = commit_meta.get("total_commits", 0)
    span = commit_meta.get("commit_span_days", 0)
    if commits >= 10 and span >= 14:
        highlights.append({"status": "pass", "text": f"Organic Timeline: {commits} commits spanning {span} days of history"})
    elif commits <= 2:
        highlights.append({"status": "fail", "text": f"Instant Dump Risk: Only {commits} commit(s) — no development history"})
    else:
        highlights.append({"status": "warn", "text": f"Limited History: {commits} commits over {span} days"})

    # Commit quality
    if d3_score >= 70:
        highlights.append({"status": "pass", "text": "Professional Commits: Uses conventional git semantic tags (feat/fix/refactor)"})
    else:
        highlights.append({"status": "warn", "text": "Generic Commit Messages: Mostly non-descriptive messages detected"})

    # Production signals
    for sig in d5_passing:
        highlights.append({"status": "pass", "text": f"Production: {sig} detected"})
    for sig in d5_failing:
        highlights.append({"status": "warn", "text": f"Missing: {sig} not found"})

    # Tutorial fingerprint
    if d4_score >= 90:
        highlights.append({"status": "pass", "text": "No Boilerplate: Zero tutorial or generic template markers detected"})
    else:
        highlights.append({"status": "fail", "text": "Template Warning: Tutorial/boilerplate fingerprints found in repo metadata"})

    return {
        "repo_full_name": f"{owner}/{repo}",
        "authenticity_score": authenticity_score,
        "quality_tier": tier_key,
        "quality_tier_label": tier["label"],
        "quality_tier_icon": tier["icon"],
        "quality_tier_color": tier["color"],
        "anomaly_score": round(anomaly_score, 2),
        "anomaly_label": (
            "Normal Developer Pattern" if anomaly_score < 0.3 else
            "Borderline Activity Pattern" if anomaly_score < 0.6 else
            "Suspicious Burst / Dump Pattern (Isolation Forest Flag)"
        ),
        "total_commits": commit_meta.get("total_commits", 0),
        "commit_span_days": commit_meta.get("commit_span_days", 0),
        "first_commit_date": commit_meta.get("first_commit_date", "Unknown"),
        "latest_commit_date": commit_meta.get("latest_commit_date", "Unknown"),
        "yearly_commits": commit_meta.get("yearly_commits", {}),
        "is_fork": commit_meta.get("is_fork", False),
        "parent_repo": commit_meta.get("parent_repo"),
        "commit_intent_distribution": intent_distribution,
        "highlights": highlights,
        "dimensions": {
            "d1_fork_origin": {
                "label": "Fork & Upstream Origin",
                "score": d1_score,
                "weight": "25%",
                "explanation": d1_explanation
            },
            "d2_commit_cadence": {
                "label": "Commit Timeline Cadence",
                "score": d2_score,
                "weight": "25%",
                "explanation": d2_explanation
            },
            "d3_commit_quality": {
                "label": "Commit Message Semantic Quality (NER)",
                "score": d3_score,
                "weight": "15%",
                "explanation": d3_explanation
            },
            "d4_tutorial_scan": {
                "label": "Tutorial & Boilerplate Scanner",
                "score": d4_score,
                "weight": "20%",
                "explanation": d4_explanation
            },
            "d5_prod_standards": {
                "label": "Production Engineering Rigor",
                "score": d5_score,
                "weight": "15%",
                "explanation": d5_explanation
            },
        },
        "live_retrieved": commit_meta.get("live_retrieved", False),
    }


async def audit_all_repositories_quality(
    github_repositories: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run Layer D authenticity audit across all candidate repositories.
    Returns aggregated report + per-repo audit results + contribution graph data.
    """
    if not github_repositories:
        return {
            "is_available": False,
            "overall_authenticity_score": 0,
            "overall_quality_tier": "unknown",
            "overall_quality_tier_label": "No Repositories Audited",
            "repo_audits": [],
            "contribution_graph": {
                "yearly_totals": {},
                "per_repo_by_year": {},
                "total_tracked_commits": 0,
                "years_active": [],
            },
            "layer_d_penalty_applied": False,
        }

    repo_audits = []
    for repo_data in github_repositories:
        owner = repo_data.get("owner", "")
        repo = repo_data.get("repo_name", "")
        if owner and repo:
            audit = await audit_repository_authenticity(owner, repo, repo_data)
            repo_audits.append(audit)

    if not repo_audits:
        return {
            "is_available": False,
            "overall_authenticity_score": 0,
            "overall_quality_tier": "unknown",
            "overall_quality_tier_label": "No Repositories Audited",
            "repo_audits": [],
            "contribution_graph": {
                "yearly_totals": {},
                "per_repo_by_year": {},
                "total_tracked_commits": 0,
                "years_active": [],
            },
            "layer_d_penalty_applied": False,
        }

    # Aggregate overall authenticity score (average across repos)
    avg_score = sum(r["authenticity_score"] for r in repo_audits) / len(repo_audits)
    avg_score = round(avg_score, 1)

    if avg_score >= 80:
        tier_key, tier_label = "production", QUALITY_TIERS["production"]["label"]
    elif avg_score >= 55:
        tier_key, tier_label = "competent", QUALITY_TIERS["competent"]["label"]
    elif avg_score >= 35:
        tier_key, tier_label = "basic", QUALITY_TIERS["basic"]["label"]
    else:
        tier_key, tier_label = "tutorial", QUALITY_TIERS["tutorial"]["label"]

    # Contribution graph
    contribution_graph = build_contribution_graph(repo_audits)

    # Layer D penalty flag: if most repos are tutorial-tier, apply note
    tutorial_count = sum(1 for r in repo_audits if r["quality_tier"] == "tutorial")
    layer_d_penalty = tutorial_count > (len(repo_audits) / 2)

    return {
        "is_available": True,
        "overall_authenticity_score": avg_score,
        "overall_quality_tier": tier_key,
        "overall_quality_tier_label": tier_label,
        "repo_audits": repo_audits,
        "contribution_graph": contribution_graph,
        "layer_d_penalty_applied": layer_d_penalty,
        "layer_d_penalty_note": (
            "⚠️ Majority of linked repositories appear to be tutorial copies or forked projects. "
            "Recruiter should ask candidate to explain their individual code contributions."
        ) if layer_d_penalty else None,
    }
