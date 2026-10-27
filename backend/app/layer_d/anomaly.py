"""
Layer D — Anomaly Detection
============================
Isolation Forest anomaly scorer for GitHub repositories.
Falls back to rule-based logic when too few repos are available.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import IsolationForest
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    logger.warning("[Layer D] scikit-learn not found; using rule-based anomaly fallback.")


# ── Feature extraction ────────────────────────────────────────────────────────

def _extract_features(repo_stats: Dict[str, Any]) -> List[float]:
    """
    Build a numeric feature vector for one repository.
    repo_stats keys: commit_count, active_days, max_day_share, lazy_ratio
    """
    n = max(repo_stats.get("commit_count", 0), 0)
    span = max(repo_stats.get("active_days", 0), 0)
    cpd = n / max(span, 1)                       # commits per day
    max_share = repo_stats.get("max_day_share", 1.0)
    lazy = repo_stats.get("lazy_ratio", 1.0)
    return [
        float(n),
        float(span),
        float(min(cpd, 50)),          # cap extreme values
        float(max_share),
        float(lazy),
    ]


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_anomaly(stats: Dict[str, Any]) -> Tuple[float, str]:
    """Simple rule-based burst / dump detector."""
    n = stats.get("commit_count", 0)
    max_share = stats.get("max_day_share", 0.0)
    lazy = stats.get("lazy_ratio", 0.0)

    if n <= 1:
        return 0.95, "Suspicious Burst / Dump Pattern"
    if max_share > 0.80 and n < 10:
        return 0.85, "Suspicious Burst / Dump Pattern"
    if lazy > 0.70 and n < 15:
        return 0.75, "Suspicious Burst / Dump Pattern"
    return 0.2, "Normal Developer Pattern"


# ── Isolation Forest ─────────────────────────────────────────────────────────

def run_anomaly_detection(repos_stats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of per-repo stat dicts, return augmented dicts with:
      anomaly_score (0–1, higher = more anomalous)
      anomaly_label ("Normal Developer Pattern" | "Suspicious Burst / Dump Pattern")

    If sklearn is unavailable or fewer than 3 repos are provided, uses rule-based
    fallback for all repos.
    """
    results = []

    use_ml = _SKLEARN_AVAILABLE and len(repos_stats) >= 3

    if use_ml:
        X = np.array([_extract_features(s) for s in repos_stats], dtype=float)
        try:
            clf = IsolationForest(contamination=0.1, random_state=42, n_estimators=100)
            clf.fit(X)
            # decision_function returns negative scores for anomalies
            raw_scores = clf.decision_function(X)         # higher = more normal
            # Normalise to 0-1 where 1 = most anomalous
            normalised = 1.0 - (raw_scores - raw_scores.min()) / (raw_scores.ptp() + 1e-9)
            predictions = clf.predict(X)                  # -1 = anomaly, 1 = normal
        except Exception as exc:
            logger.warning("[Layer D] IsolationForest failed: %s; falling back to rules.", exc)
            use_ml = False

    for i, stats in enumerate(repos_stats):
        if use_ml:
            score = float(np.clip(normalised[i], 0.0, 1.0))
            label = ("Suspicious Burst / Dump Pattern" if predictions[i] == -1
                     else "Normal Developer Pattern")
        else:
            score, label = _rule_anomaly(stats)

        results.append({**stats, "anomaly_score": round(score, 3), "anomaly_label": label})

    return results
