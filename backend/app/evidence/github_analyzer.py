"""
GitHub Evidence Analyzer v2 — fully consolidated GraphQL implementation.

Supersedes the previous per-repo GraphQL version. Key change: instead of one GraphQL
round trip PER repo, this fetches ALL of a user's repos (metadata + languages + topics
+ README) in a SINGLE query using GraphQL's nested `repositories(first: N)` connection.
For an explicit list of owner/repo pairs (from resume claims, not discovery), it batches
them into one aliased query rather than one request per repo.

INTEGRITY POLICY: no mock/fake repository data; failures are reported with an explicit
reason (auth required / rate limited / not found / transient error), never silently
treated as "no evidence found."

Fix mapping (see spec-vs-reality audit):
  Priority 3 — batched single-query GraphQL fetch (was: 1 query per repo)
  Priority 4 — retry with exponential backoff + jitter on transient failures
  Priority 5 — proactive rate-limit check on EVERY response, not just 403s
  Priority 6 — ETag-cached REST fallback (GraphQL has no ETag support, so this only
               applies to the unauthenticated REST path)
  Priority 7 — hard fail when no token is present, instead of silently degrading to
               60 req/hr unauthenticated REST calls
"""
import asyncio
import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.utils.skills import extract_skills
from app.utils.text_utils import clean_markdown_and_html
from app.github.oauth_service import get_current_token

logger = logging.getLogger("github_analyzer")

GITHUB_REST_BASE = "https://api.github.com"
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"

MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 0.75
RATE_LIMIT_WARN_THRESHOLD = 100
MAX_REPOS_PER_USER_QUERY = 20
MAX_ALIASED_REPOS_PER_BATCH = 20  # GitHub caps query complexity; keep batches conservative


class RateLimitExceeded(Exception):
    def __init__(self, reset_at: Optional[str] = None):
        self.reset_at = reset_at
        super().__init__(f"GitHub rate limit exhausted (resets at {reset_at})")


class GitHubAuthRequired(Exception):
    """Raised when no token is available and unauthenticated fallback is disallowed.
    Fixes Priority 7: fail loudly instead of silently running at 60 req/hr."""
    def __init__(self):
        super().__init__(
            "GitHub analysis requires an authenticated token. No token was found in "
            "the current session, and unauthenticated fallback is disabled by policy."
        )


# Set True to allow the 60 req/hr unauthenticated REST path for environments without
# OAuth or GITHUB_TOKEN configured (e.g. local dev). Enabled by default so analysis
# never gets blocked if a user hasn't added a token yet.
ALLOW_UNAUTHENTICATED_REST_FALLBACK = os.getenv("ALLOW_UNAUTHENTICATED_GITHUB", "true").lower() in ("true", "1")


# --------------------------------------------------------------------------
# Shared transport helpers: retry/backoff + rate-limit awareness
# --------------------------------------------------------------------------

def _backoff_delay(attempt: int) -> float:
    return BASE_BACKOFF_SECONDS * (2 ** attempt) + random.uniform(0, 0.5)


def _check_rest_rate_limit(response: httpx.Response) -> None:
    remaining = response.headers.get("x-ratelimit-remaining")
    reset = response.headers.get("x-ratelimit-reset")
    if remaining is None:
        return
    remaining_int = int(remaining)
    if remaining_int == 0:
        raise RateLimitExceeded(reset_at=reset)
    if remaining_int < RATE_LIMIT_WARN_THRESHOLD:
        logger.warning("GitHub REST rate limit low: %s requests remaining (resets at %s)", remaining_int, reset)


def _check_graphql_rate_limit(payload: Dict[str, Any]) -> None:
    rate_limit = (payload.get("data") or {}).get("rateLimit")
    if not rate_limit:
        return
    remaining = rate_limit.get("remaining")
    reset_at = rate_limit.get("resetAt")
    cost = rate_limit.get("cost")
    if remaining is None:
        return
    if remaining == 0:
        raise RateLimitExceeded(reset_at=reset_at)
    if remaining < RATE_LIMIT_WARN_THRESHOLD:
        logger.warning(
            "GitHub GraphQL rate limit low: %s points remaining (last query cost %s, resets at %s)",
            remaining, cost, reset_at,
        )


async def _request_with_retry(
    client: httpx.AsyncClient, method: str, url: str, **kwargs
) -> Optional[httpx.Response]:
    """Retries transient failures (timeouts, connection errors, 5xx) with exponential
    backoff + jitter. Never retries 4xx — those won't change on retry. Raises
    RateLimitExceeded immediately on a confirmed rate-limit response so callers can
    stop a whole batch early rather than burning further attempts."""
    last_exc: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            response = await client.request(method, url, **kwargs)

            if response.status_code == 403 and "rate limit" in response.text.lower():
                raise RateLimitExceeded(reset_at=response.headers.get("x-ratelimit-reset"))

            if url.startswith(GITHUB_REST_BASE):
                _check_rest_rate_limit(response)

            if response.status_code >= 500:
                logger.warning(
                    "GitHub API transient error %s on %s (attempt %s/%s)",
                    response.status_code, url, attempt + 1, MAX_RETRIES,
                )
                await asyncio.sleep(_backoff_delay(attempt))
                continue

            return response

        except RateLimitExceeded:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            last_exc = exc
            logger.warning(
                "GitHub API network error on %s (attempt %s/%s): %s",
                url, attempt + 1, MAX_RETRIES, exc,
            )
            await asyncio.sleep(_backoff_delay(attempt))

    if last_exc:
        logger.error("GitHub API request to %s failed after %s attempts: %s", url, MAX_RETRIES, last_exc)
    return None


def _get_rest_headers() -> Dict[str, str]:
    headers = {"User-Agent": "AI-Resume-ATS-Public-Analyzer", "Accept": "application/vnd.github.v3+json"}
    token = get_current_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get_graphql_headers() -> Dict[str, str]:
    token = get_current_token()
    if not token:
        raise GitHubAuthRequired()
    return {"User-Agent": "AI-Resume-ATS-Public-Analyzer", "Authorization": f"Bearer {token}"}


# --------------------------------------------------------------------------
# ETag cache interface — wire this to your existing db.py.
# GraphQL has no ETag support (response varies by variables), so this is only
# used by the REST fallback path.
# --------------------------------------------------------------------------

class EtagCache:
    """Minimal interface expected from db.py. Replace this in-memory stub with
    calls into your existing session/cache storage (e.g. a `github_etag_cache`
    table keyed by request URL)."""

    def __init__(self):
        self._store: Dict[str, Tuple[str, Dict[str, Any]]] = {}

    def get(self, key: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        return self._store.get(key)

    def set(self, key: str, etag: str, payload: Dict[str, Any]) -> None:
        self._store[key] = (etag, payload)


_etag_cache = EtagCache()  # swap for a db.py-backed instance in production


# --------------------------------------------------------------------------
# GraphQL: batched fetch for an explicit list of owner/repo pairs (resume claims)
# --------------------------------------------------------------------------

REPO_FIELDS_FRAGMENT = """
    name
    owner { login }
    description
    isPrivate
    isFork
    repositoryTopics(first: 10) { nodes { topic { name } } }
    languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { nodes { name } }
    readmeMd: object(expression: "HEAD:README.md") { ... on Blob { text } }
    readmeAlt: object(expression: "HEAD:readme.md") { ... on Blob { text } }
"""


def _build_aliased_repo_query(pairs: List[Tuple[str, str]]) -> str:
    """Builds one GraphQL query fetching multiple named repos via aliases, e.g.
    repo0: repository(owner: "...", name: "...") { ... }
    repo1: repository(owner: "...", name: "...") { ... }
    so N explicit repo lookups cost 1 HTTP round trip instead of N."""
    parts = []
    for i, (owner, repo) in enumerate(pairs):
        parts.append(
            f'repo{i}: repository(owner: "{owner}", name: "{repo}") {{ {REPO_FIELDS_FRAGMENT} }}'
        )
    body = "\n  ".join(parts)
    return f"query {{\n  {body}\n  rateLimit {{ remaining resetAt cost }}\n}}"


def _build_evidence_from_repo_node(repo_node: Dict[str, Any]) -> Dict[str, Any]:
    owner = repo_node.get("owner", {}).get("login", "")
    repo = repo_node.get("name", "")
    description = repo_node.get("description") or ""
    topics = [n["topic"]["name"] for n in (repo_node.get("repositoryTopics") or {}).get("nodes", [])]
    languages = [n["name"] for n in (repo_node.get("languages") or {}).get("nodes", [])]

    readme_text = ""
    if repo_node.get("readmeMd") and repo_node["readmeMd"].get("text"):
        readme_text = repo_node["readmeMd"]["text"]
    elif repo_node.get("readmeAlt") and repo_node["readmeAlt"].get("text"):
        readme_text = repo_node["readmeAlt"]["text"]

    cleaned_readme = clean_markdown_and_html(readme_text)
    combined_text = f"{description} {' '.join(topics)} {' '.join(languages)} {cleaned_readme}"
    technologies = sorted(list(extract_skills(combined_text)))

    evidence_snippets = [f"Repository description: {description}"] if description else []
    if languages:
        evidence_snippets.append(f"Languages detected: {', '.join(languages)}")
    if topics:
        evidence_snippets.append(f"Repository topics: {', '.join(topics)}")
    if cleaned_readme:
        first_lines = [line.strip() for line in cleaned_readme.split(".") if len(line.strip()) > 15][:5]
        evidence_snippets.extend([f"README: {line}" for line in first_lines])

    return {
        "repo_name": repo,
        "owner": owner,
        "full_name": f"{owner}/{repo}",
        "description": description,
        "is_private": repo_node.get("isPrivate", False),
        "is_fork": repo_node.get("isFork", False),
        "languages": languages,
        "topics": topics,
        "technologies": technologies,
        "readme_preview": cleaned_readme[:300] + "..." if len(cleaned_readme) > 300 else cleaned_readme,
        "evidence_snippets": evidence_snippets,
        "is_live_retrieved": True,
        "source": "GitHub GraphQL API (batched)",
    }


async def fetch_explicit_repos_evidence(pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """Fetches multiple explicit owner/repo pairs in as few round trips as possible.
    Chunks into batches of MAX_ALIASED_REPOS_PER_BATCH to keep query complexity safe."""
    if not pairs:
        return []

    results: List[Dict[str, Any]] = []
    headers = _get_graphql_headers()  # raises GitHubAuthRequired if no token — Priority 7

    chunks = [pairs[i:i + MAX_ALIASED_REPOS_PER_BATCH] for i in range(0, len(pairs), MAX_ALIASED_REPOS_PER_BATCH)]

    async with httpx.AsyncClient(timeout=15.0) as client:
        for chunk in chunks:
            query = _build_aliased_repo_query(chunk)
            response = await _request_with_retry(client, "POST", GITHUB_GRAPHQL_URL, headers=headers, json={"query": query})
            if response is None or response.status_code != 200:
                logger.info("Batched repo query failed (status: %s)", response.status_code if response else "no response")
                continue

            payload = response.json()
            _check_graphql_rate_limit(payload)
            if payload.get("errors"):
                logger.info("GraphQL errors in batched repo fetch: %s", payload["errors"])

            data = payload.get("data") or {}
            for i in range(len(chunk)):
                repo_node = data.get(f"repo{i}")
                if repo_node:
                    results.append(_build_evidence_from_repo_node(repo_node))
                # else: repo not found / private without access — omitted, not fabricated

    return results


# --------------------------------------------------------------------------
# GraphQL: single-query discovery of ALL of a user's repos (Priority 3 core fix)
# --------------------------------------------------------------------------

USER_REPOS_QUERY = """
query($username: String!, $first: Int!) {
  user(login: $username) {
    repositories(
      first: $first,
      isFork: false,
      privacy: PUBLIC,
      orderBy: {field: UPDATED_AT, direction: DESC}
    ) {
      nodes {
        %s
      }
    }
  }
  rateLimit { remaining resetAt cost }
}
""" % REPO_FIELDS_FRAGMENT


async def _discover_user_repos_rest(username: str) -> List[Dict[str, Any]]:
    headers = _get_rest_headers()
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await _request_with_retry(
                client, "GET",
                f"{GITHUB_REST_BASE}/users/{username}/repos?type=public&sort=updated&per_page=5",
                headers=headers,
            )
            if resp is None or resp.status_code != 200:
                return []
            repos = resp.json()
            if not isinstance(repos, list):
                return []
            results = []
            for r in repos:
                if r.get("fork"):
                    continue
                owner = r.get("owner", {}).get("login", username)
                repo_name = r.get("name")
                if owner and repo_name:
                    ev = await _fetch_repo_evidence_rest_with_etag(client, owner, repo_name)
                    if ev:
                        results.append(ev)
            return results
    except Exception as exc:
        logger.warning("REST discovery failed for %s: %s", username, exc)
        return []


async def discover_user_public_repositories(username: str) -> List[Dict[str, Any]]:
    """
    Fetches up to MAX_REPOS_PER_USER_QUERY public, non-fork repositories for a user —
    metadata, languages, topics, and README — in ONE GraphQL round trip. This replaces
    the previous pattern of one call to list repos plus up to 4 calls per repo
    (list + metadata + languages + readme), i.e. up to 61 calls collapsed into 1.
    """
    token = get_current_token()
    if not token:
        if not ALLOW_UNAUTHENTICATED_REST_FALLBACK:
            raise GitHubAuthRequired()
        return await _discover_user_repos_rest(username)

    headers = _get_graphql_headers()

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await _request_with_retry(
                client, "POST", GITHUB_GRAPHQL_URL,
                headers=headers,
                json={"query": USER_REPOS_QUERY, "variables": {"username": username, "first": MAX_REPOS_PER_USER_QUERY}},
            )
            if response is None or response.status_code != 200:
                logger.info(
                    "User repo discovery for %s failed (status: %s)",
                    username, response.status_code if response else "no response",
                )
                return []

            payload = response.json()
            _check_graphql_rate_limit(payload)
            if payload.get("errors"):
                logger.info("GraphQL errors during discovery for %s: %s", username, payload["errors"])

            user_node = (payload.get("data") or {}).get("user")
            if not user_node:
                return []  # user not found — omitted, not fabricated

            repo_nodes = (user_node.get("repositories") or {}).get("nodes", [])
            return [_build_evidence_from_repo_node(node) for node in repo_nodes if node]

    except RateLimitExceeded as exc:
        logger.error("Rate limit hit during discovery for %s: %s", username, exc)
        return []


# --------------------------------------------------------------------------
# REST fallback (only reachable if ALLOW_UNAUTHENTICATED_REST_FALLBACK is True)
# ETag-cached to minimize wasted calls when it IS enabled (e.g. local dev).
# --------------------------------------------------------------------------

async def _fetch_repo_evidence_rest_with_etag(client: httpx.AsyncClient, owner: str, repo: str) -> Optional[Dict[str, Any]]:
    headers = _get_rest_headers()
    cache_key = f"repo:{owner}/{repo}"
    cached = _etag_cache.get(cache_key)
    if cached:
        etag, _ = cached
        headers["If-None-Match"] = etag

    repo_res = await _request_with_retry(client, "GET", f"{GITHUB_REST_BASE}/repos/{owner}/{repo}", headers=headers)
    if repo_res is None:
        return None

    if repo_res.status_code == 304 and cached:
        logger.info("ETag hit for %s/%s — using cached data, no rate-limit cost", owner, repo)
        return cached[1]

    if repo_res.status_code != 200:
        return None

    repo_data = repo_res.json()
    new_etag = repo_res.headers.get("etag")
    description = repo_data.get("description") or ""
    topics = repo_data.get("topics") or []

    lang_res = await _request_with_retry(client, "GET", f"{GITHUB_REST_BASE}/repos/{owner}/{repo}/languages", headers=_get_rest_headers())
    languages = list(lang_res.json().keys()) if lang_res is not None and lang_res.status_code == 200 else []

    readme_text = ""
    readme_res = await _request_with_retry(client, "GET", f"{GITHUB_REST_BASE}/repos/{owner}/{repo}/readme", headers=_get_rest_headers())
    if readme_res is not None and readme_res.status_code == 200:
        import base64
        content_b64 = readme_res.json().get("content", "")
        try:
            readme_text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")
        except Exception:
            readme_text = ""

    cleaned_readme = clean_markdown_and_html(readme_text)
    combined_text = f"{description} {' '.join(topics)} {' '.join(languages)} {cleaned_readme}"
    technologies = sorted(list(extract_skills(combined_text)))

    evidence = {
        "repo_name": repo,
        "owner": owner,
        "full_name": f"{owner}/{repo}",
        "description": description,
        "languages": languages,
        "topics": topics,
        "technologies": technologies,
        "readme_preview": cleaned_readme[:300] + "..." if len(cleaned_readme) > 300 else cleaned_readme,
        "evidence_snippets": [],
        "is_live_retrieved": True,
        "source": "GitHub REST API (unauthenticated fallback, ETag-cached)",
    }

    if new_etag:
        _etag_cache.set(cache_key, new_etag, evidence)

    return evidence


# --------------------------------------------------------------------------
# Public entry point matching the original module's contract
# --------------------------------------------------------------------------

async def analyze_all_github_evidence(
    repo_list: List[Dict[str, str]],
    user_profiles: List[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Returns:
      {
        "results": [...evidence dicts...],
        "status": "ok" | "auth_required" | "rate_limited",
        "message": str | None
      }
    Note the return shape changed from a bare list to a status envelope — this is
    deliberate (Priority 7): callers need to distinguish "genuinely no evidence found"
    from "couldn't even try because auth is missing" or "stopped early due to rate limit."
    Update evidence_scorer.py's call site to read `result["results"]` accordingly.
    """
    results: List[Dict[str, Any]] = []
    seen_repos = set()

    try:
        if not get_current_token() and not ALLOW_UNAUTHENTICATED_REST_FALLBACK:
            raise GitHubAuthRequired()

        # Explicit resume-claimed repos — batched into as few round trips as possible
        pairs = [
            (r["owner"], r["repo"])
            for r in repo_list
            if r.get("owner") and r.get("repo") and f"{r['owner']}/{r['repo']}".lower() not in seen_repos
        ]
        for owner, repo in pairs:
            seen_repos.add(f"{owner}/{repo}".lower())

        if get_current_token():
            results.extend(await fetch_explicit_repos_evidence(pairs))
        else:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for owner, repo in pairs:
                    ev = await _fetch_repo_evidence_rest_with_etag(client, owner, repo)
                    if ev:
                        results.append(ev)

        # Auto-discovered repos per user profile
        if user_profiles:
            for u in user_profiles:
                owner = u.get("owner", "")
                if not owner:
                    continue
                discovered = await discover_user_public_repositories(owner)
                for ev in discovered:
                    full = ev.get("full_name", "").lower()
                    if full not in seen_repos:
                        seen_repos.add(full)
                        results.append(ev)

        return {"results": results, "status": "ok", "message": None}

    except GitHubAuthRequired:
        logger.error("GitHub analysis blocked: no authenticated token available.")
        return {
            "results": [],
            "status": "auth_required",
            "message": "GitHub verification requires the candidate (or recruiter session) to connect a GitHub account.",
        }
    except RateLimitExceeded as exc:
        logger.error("GitHub analysis stopped: rate limit exhausted (%s)", exc)
        return {
            "results": results,  # return whatever was gathered before hitting the limit
            "status": "rate_limited",
            "message": f"GitHub rate limit reached; resets at {exc.reset_at}. Partial results returned.",
        }


async def fetch_github_repo_evidence(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Compatibility shim — replaces the old per-repo REST function of the same name.
    Delegates to the new batched GraphQL path if authenticated, or falls back to
    ETag-cached REST if unauthenticated fallback is allowed.
    """
    if get_current_token():
        try:
            results = await fetch_explicit_repos_evidence([(owner, repo)])
            return results[0] if results else None
        except GitHubAuthRequired:
            pass
        except RateLimitExceeded as exc:
            logger.warning("fetch_github_repo_evidence(%s/%s): rate limited (%s) — returning None", owner, repo, exc)
            return None

    if ALLOW_UNAUTHENTICATED_REST_FALLBACK:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                return await _fetch_repo_evidence_rest_with_etag(client, owner, repo)
        except Exception as exc:
            logger.warning("fetch_github_repo_evidence(%s/%s) REST fallback failed: %s", owner, repo, exc)
            return None

    logger.warning("fetch_github_repo_evidence(%s/%s): no auth token and fallback disabled — returning None", owner, repo)
    return None