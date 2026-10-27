"""
Layer D — GitHub API Client
============================
Async HTTP client for GitHub REST API v3.
Handles auth, rate-limits, caching and resilient error handling.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ── Auth ──────────────────────────────────────────────────────────────────────
GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
_AUTH_HEADERS: Dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    _AUTH_HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"

# ── In-memory response cache (username → {key: (payload, expire_ts)}) ─────────
_CACHE: Dict[str, Dict[str, Tuple[Any, float]]] = {}
_CACHE_TTL_S = 6 * 3600  # 6 hours

BASE_URL = "https://api.github.com"
TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# ── Semaphore (shared across all coroutines per analysis run) ─────────────────
_SEM = asyncio.Semaphore(6)


def _cache_get(ns: str, key: str) -> Optional[Any]:
    bucket = _CACHE.get(ns, {})
    entry = bucket.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _cache_set(ns: str, key: str, value: Any) -> None:
    _CACHE.setdefault(ns, {})[key] = (value, time.time() + _CACHE_TTL_S)


async def _get(client: httpx.AsyncClient, url: str, params: Optional[Dict] = None) -> Any:
    """Single GET with rate-limit awareness. Raises on hard failure."""
    resp = await client.get(url, params=params, headers=_AUTH_HEADERS, timeout=TIMEOUT)
    if resp.status_code in (403, 429):
        raise RuntimeError(f"GitHub rate-limit hit ({resp.status_code}): {url}")
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


# ── Public helpers ─────────────────────────────────────────────────────────────

async def fetch_user_repos(username: str, client: httpx.AsyncClient) -> List[Dict]:
    """Return public repos for *username*, sorted by last update."""
    cached = _cache_get(username, "repos")
    if cached is not None:
        return cached
    data = await _get(client, f"{BASE_URL}/users/{username}/repos",
                      params={"per_page": 100, "sort": "updated", "type": "owner"})
    result: List[Dict] = data if isinstance(data, list) else []
    _cache_set(username, "repos", result)
    return result


async def fetch_file_tree(owner: str, repo: str, branch: str,
                          client: httpx.AsyncClient) -> List[str]:
    """Return flat list of file paths for *repo* on *branch*."""
    cache_key = f"tree:{owner}/{repo}/{branch}"
    cached = _cache_get(owner, cache_key)
    if cached is not None:
        return cached
    data = await _get(client, f"{BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}",
                      params={"recursive": "1"})
    if not data:
        return []
    paths = [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]
    _cache_set(owner, cache_key, paths)
    return paths


async def fetch_commits(owner: str, repo: str, client: httpx.AsyncClient) -> List[Dict]:
    """Return up to 100 commits for *repo*."""
    cache_key = f"commits:{owner}/{repo}"
    cached = _cache_get(owner, cache_key)
    if cached is not None:
        return cached
    data = await _get(client, f"{BASE_URL}/repos/{owner}/{repo}/commits",
                      params={"per_page": 100})
    result: List[Dict] = data if isinstance(data, list) else []
    _cache_set(owner, cache_key, result)
    return result


async def fetch_readme(owner: str, repo: str, client: httpx.AsyncClient) -> Optional[str]:
    """Return decoded README text or None."""
    cache_key = f"readme:{owner}/{repo}"
    cached = _cache_get(owner, cache_key)
    if cached is not None:
        return cached
    data = await _get(client, f"{BASE_URL}/repos/{owner}/{repo}/readme")
    if not data:
        return None
    try:
        text = base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    except Exception:
        text = None
    _cache_set(owner, cache_key, text)
    return text


async def gather_repo_data(
    owner: str,
    repo_info: Dict,
    username: str,
    client: httpx.AsyncClient,
) -> Dict:
    """
    Concurrently fetch tree + commits + README for one repo.
    Returns a dict with all raw data or error flags.
    """
    name = repo_info["name"]
    branch = repo_info.get("default_branch", "main")

    async def safe(coro, label: str):
        try:
            async with _SEM:
                return await coro
        except Exception as exc:
            logger.warning("[Layer D] %s/%s fetch '%s' failed: %s", owner, name, label, exc)
            return None

    tree_task = safe(fetch_file_tree(owner, name, branch, client), "tree")
    commits_task = safe(fetch_commits(owner, name, client), "commits")
    readme_task = safe(fetch_readme(owner, name, client), "readme")

    tree, commits, readme = await asyncio.gather(tree_task, commits_task, readme_task)

    return {
        "name": name,
        "full_name": f"{owner}/{name}",
        "fork": repo_info.get("fork", False),
        "archived": repo_info.get("archived", False),
        "size": repo_info.get("size", 0),
        "default_branch": branch,
        "description": repo_info.get("description", ""),
        "pushed_at": repo_info.get("pushed_at"),
        "tree": tree or [],
        "commits": commits or [],
        "readme": readme,
        "tree_available": tree is not None,
        "commits_available": commits is not None,
    }
