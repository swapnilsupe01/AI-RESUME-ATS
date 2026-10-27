"""
Layer D — FastAPI Router
=========================
Endpoint: POST /api/layer-d/analyze
Accepts { "username": "octocat" } and returns the full Layer D report.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from app.layer_d import github_client as gh
from app.layer_d.checks import run_file_checks, run_commit_checks, test_to_source_ratio
from app.layer_d.anomaly import run_anomaly_detection
from app.layer_d.scoring import (
    compute_repo_score, compute_overall_score, compute_global_flags,
    build_repo_flags, _tier,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/layer-d", tags=["Layer D"])

MAX_REPOS = 8          # max repos to analyse deeply
MIN_REPOS = 1          # minimum to attempt scoring
FORK_BUDGET = 3        # forks counted but not scored


# ── Request / Response models ─────────────────────────────────────────────────

class LayerDRequest(BaseModel):
    username: str
    candidate_login: Optional[str] = None   # fallback to username if omitted

    @field_validator("username")
    @classmethod
    def _clean(cls, v: str) -> str:
        v = v.strip().lstrip("@")
        if not v:
            raise ValueError("username must not be empty")
        return v


# ── Core analysis ─────────────────────────────────────────────────────────────

async def _analyze(username: str, candidate_login: str) -> Dict[str, Any]:
    """Full Layer D analysis pipeline. Returns the report dict."""
    t0 = time.monotonic()

    async with httpx.AsyncClient() as client:
        # Step 1: Fetch all repos
        try:
            all_repos = await gh.fetch_user_repos(username, client)
        except RuntimeError as exc:
            if "rate-limit" in str(exc).lower():
                raise HTTPException(status_code=429, detail=str(exc))
            raise HTTPException(status_code=502, detail=str(exc))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail=f"GitHub user '{username}' not found or has no public repos.",
                )
            raise

        if not all_repos:
            raise HTTPException(
                status_code=404,
                detail=f"No public repositories found for '{username}'.",
            )

        # Separate forks from scoreable repos
        forks = [r for r in all_repos if r.get("fork")]
        scoreable = [
            r for r in all_repos
            if not r.get("fork") and not r.get("archived") and r.get("size", 0) > 0
        ]

        if not scoreable:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"'{username}' has {len(all_repos)} public repo(s) but all are forks, "
                    "archived, or empty — nothing to score."
                ),
            )

        # Pick top N by updated_at
        to_scan = scoreable[:MAX_REPOS]

        # Step 2: Fetch tree + commits + README in parallel
        tasks = [gh.gather_repo_data(username, r, username, client) for r in to_scan]
        raw_repos: List[Dict] = await asyncio.gather(*tasks)

    # Step 3 & 4: Run checks + compute stats for anomaly detection
    repos_stats: List[Dict] = []
    repos_output: List[Dict] = []

    for raw in raw_repos:
        # File checks
        file_checks = run_file_checks(raw["tree"], raw.get("readme"))
        # Commit checks
        commit_checks, intent_counts = run_commit_checks(
            raw["commits"], candidate_login
        )
        # Test-to-source ratio
        tsr, tsr_status = test_to_source_ratio(raw["tree"])

        # Per-repo score
        repo_score, raw_totals = compute_repo_score(file_checks, commit_checks)

        # Stats for anomaly
        n = len(raw["commits"])
        dates_per_day: Dict[str, int] = {}
        lazy = intent_counts.get("lazy", 0) + intent_counts.get("unknown", 0)
        for c in raw["commits"]:
            d = (c.get("commit", {}).get("author") or {}).get("date", "")[:10]
            if d:
                dates_per_day[d] = dates_per_day.get(d, 0) + 1
        max_day = max(dates_per_day.values(), default=0)
        max_share = max_day / max(n, 1)
        active_days = len(dates_per_day)
        lazy_ratio = lazy / max(n, 1)

        repos_stats.append({
            "name": raw["name"],
            "commit_count": n,
            "active_days": active_days,
            "max_day_share": max_share,
            "lazy_ratio": lazy_ratio,
            "repo_score": repo_score,
        })

        repos_output.append({
            "name": raw["name"],
            "score": repo_score,
            "commits": n,
            "span_days": active_days,
            "commit_intents": intent_counts,
            "test_to_source_ratio": round(tsr, 3),
            "checks": {
                cid: v["status"] for cid, v in {**file_checks, **commit_checks}.items()
            },
            "_file_checks": file_checks,
            "_commit_checks": commit_checks,
        })

    # Anomaly detection across all repos
    augmented = run_anomaly_detection(repos_stats)
    for i, aug in enumerate(augmented):
        repos_output[i]["anomaly_score"] = aug["anomaly_score"]
        repos_output[i]["anomaly_label"] = aug["anomaly_label"]

    # Overall score (best 5)
    repo_scores = [r["score"] for r in repos_output]
    overall = compute_overall_score(repo_scores)

    # Global flags
    all_repo_infos = [*to_scan, *forks]
    repos_data_for_flags = [
        {"file_checks": r.pop("_file_checks"), "commit_checks": r.pop("_commit_checks")}
        for r in repos_output
    ]
    global_flags = compute_global_flags(repos_data_for_flags, all_repo_infos)

    # Per-repo flags
    for i, raw in enumerate(raw_repos):
        repo_out = repos_output[i]
        rd = repos_data_for_flags[i]
        repo_out["flags"] = build_repo_flags(rd["file_checks"], rd["commit_checks"])

    elapsed = round(time.monotonic() - t0, 2)
    logger.info("[Layer D] %s — score=%d tier=%s time=%.2fs repos=%d",
                username, overall, _tier(overall), elapsed, len(repos_output))

    return {
        "layer": "D",
        "username": username,
        "authenticity_score": overall,
        "tier": _tier(overall),
        "scan_time_seconds": elapsed,
        "repos_scanned": len(repos_output),
        "forks_skipped": len(forks),
        "global_flags": global_flags,
        "repos": repos_output,
    }


# ── FastAPI endpoint ──────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_github_profile(body: LayerDRequest) -> JSONResponse:
    """
    **Layer D — Code Quality & Authenticity Forensics**

    Analyse a candidate's public GitHub profile and return:
    - Overall authenticity score (0–100) with tier label
    - Global pass/warn/fail flags with actionable fixes
    - Per-repository audit: score, commit intents, anomaly detection, and check states
    """
    login = body.candidate_login or body.username
    result = await _analyze(body.username, login)
    return JSONResponse(content=result)


@router.get("/health")
async def layer_d_health():
    """Layer D health check."""
    return {"layer": "D", "status": "ok", "sklearn": _sklearn_available()}


def _sklearn_available() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False
