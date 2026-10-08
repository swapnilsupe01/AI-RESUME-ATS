"""
GitHub Synchronized Provenance Database Manager.
Caches public GitHub data only, strictly keyed by username (login), with TTL.
PRIVACY GUARANTEE: Never stores resume content, candidate names, or candidate emails.
Only public GitHub metadata (login, profile URL, contribution counts, public repos) is persisted.
"""
import os
import sqlite3
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "github_provenance.db")

# Cache time-to-live: 24 hours for public GitHub metadata
GITHUB_CACHE_TTL_SECONDS = 86400


def get_db_connection() -> sqlite3.Connection:
    """Get SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_github_db():
    """Initialize SQLite database tables for verified public GitHub evidence only."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. github_accounts (public profile metadata only, keyed by login / user_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_user_id INTEGER UNIQUE,
        login TEXT NOT NULL UNIQUE,
        profile_url TEXT NOT NULL,
        ownership_verified BOOLEAN NOT NULL DEFAULT 0,
        verified_at TEXT,
        created_at TEXT NOT NULL,
        retrieved_at TEXT
    )
    """)

    # 2. github_contributions (public contribution graph metrics only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_user_id INTEGER,
        login TEXT NOT NULL,
        date TEXT NOT NULL,
        year TEXT NOT NULL,
        contribution_count INTEGER NOT NULL,
        contribution_level TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'github_graphql_api',
        retrieved_at TEXT NOT NULL,
        UNIQUE(login, date)
    )
    """)

    # 3. github_yearly_stats (public contribution totals only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_yearly_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_user_id INTEGER,
        login TEXT NOT NULL,
        year TEXT NOT NULL,
        total_contributions INTEGER NOT NULL,
        restricted_contributions INTEGER DEFAULT 0,
        source TEXT NOT NULL DEFAULT 'github_graphql_api',
        retrieved_at TEXT NOT NULL,
        UNIQUE(login, year)
    )
    """)

    # 4. github_repository_contributions (public repo stats only)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_repository_contributions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_user_id INTEGER,
        login TEXT NOT NULL,
        year TEXT NOT NULL,
        repository_id TEXT,
        repository_name TEXT NOT NULL,
        repository_url TEXT,
        commit_count INTEGER NOT NULL,
        is_private BOOLEAN DEFAULT 0,
        primary_language TEXT,
        source TEXT NOT NULL DEFAULT 'github_graphql_api',
        retrieved_at TEXT NOT NULL,
        UNIQUE(login, year, repository_name)
    )
    """)

    conn.commit()
    conn.close()


def purge_expired_cache(ttl_seconds: int = GITHUB_CACHE_TTL_SECONDS):
    """Purge cached GitHub data older than TTL to ensure stale records are removed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=ttl_seconds)).isoformat()
    try:
        cursor.execute("DELETE FROM github_contributions WHERE retrieved_at < ?", (cutoff,))
        cursor.execute("DELETE FROM github_yearly_stats WHERE retrieved_at < ?", (cutoff,))
        cursor.execute("DELETE FROM github_repository_contributions WHERE retrieved_at < ?", (cutoff,))
        cursor.execute("DELETE FROM github_accounts WHERE retrieved_at IS NOT NULL AND retrieved_at < ?", (cutoff,))
        conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def is_cache_valid(login: str, ttl_seconds: int = GITHUB_CACHE_TTL_SECONDS) -> bool:
    """Check if cached public data for username is still within TTL."""
    if not login:
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT retrieved_at FROM github_accounts WHERE LOWER(login) = LOWER(?)", (login.strip(),))
    row = cursor.fetchone()
    conn.close()
    if not row or not row["retrieved_at"]:
        return False
    try:
        retrieved = datetime.fromisoformat(row["retrieved_at"].replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - retrieved).total_seconds()
        return age < ttl_seconds
    except Exception:
        return False


def save_verified_account(
    github_user_id: int,
    login: str,
    profile_url: str,
    ownership_verified: bool,
    verified_at: Optional[str] = None
):
    """
    Upsert verified public GitHub account metadata.
    Strictly accepts only public GitHub identifiers: user_id, username (login), profile_url.
    Never accepts resume data, names, or emails.
    """
    clean_login = str(login).strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    verified_at_val = verified_at or now_iso

    cursor.execute("""
    INSERT INTO github_accounts (github_user_id, login, profile_url, ownership_verified, verified_at, created_at, retrieved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(login) DO UPDATE SET
        github_user_id=excluded.github_user_id,
        profile_url=excluded.profile_url,
        ownership_verified=excluded.ownership_verified,
        verified_at=excluded.verified_at,
        retrieved_at=excluded.retrieved_at
    """, (github_user_id, clean_login, profile_url, 1 if ownership_verified else 0, verified_at_val, now_iso, now_iso))

    conn.commit()
    conn.close()


def get_verified_account(login: str, enforce_ttl: bool = True) -> Optional[Dict[str, Any]]:
    """Retrieve verified GitHub public account by username (login), respecting TTL."""
    if not login:
        return None
    clean_login = str(login).strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM github_accounts WHERE LOWER(login) = LOWER(?)", (clean_login,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    data = dict(row)
    if enforce_ttl and data.get("retrieved_at"):
        try:
            retrieved = datetime.fromisoformat(data["retrieved_at"].replace("Z", "+00:00"))
            if (datetime.now(timezone.utc) - retrieved).total_seconds() > GITHUB_CACHE_TTL_SECONDS:
                return None
        except Exception:
            pass
    return data


def save_contribution_days(login: str, github_user_id: Optional[int], days: List[Dict[str, Any]], retrieved_at: str):
    """Save batch of daily contribution records with source and timestamp provenance."""
    if not days or not login:
        return
    clean_login = str(login).strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    records = []
    for d in days:
        date_str = d.get("date")
        year_str = date_str[:4] if date_str and len(date_str) >= 4 else "2026"
        records.append((
            github_user_id,
            clean_login,
            date_str,
            year_str,
            d.get("contributionCount", 0),
            d.get("contributionLevel", "NONE"),
            "github_graphql_api",
            retrieved_at
        ))

    cursor.executemany("""
    INSERT INTO github_contributions (github_user_id, login, date, year, contribution_count, contribution_level, source, retrieved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(login, date) DO UPDATE SET
        contribution_count=excluded.contribution_count,
        contribution_level=excluded.contribution_level,
        retrieved_at=excluded.retrieved_at
    """, records)

    conn.commit()
    conn.close()


def save_yearly_stats(login: str, github_user_id: Optional[int], year: str, total: int, restricted: int, retrieved_at: str):
    """Save yearly total contributions with provenance."""
    if not login:
        return
    clean_login = str(login).strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO github_yearly_stats (github_user_id, login, year, total_contributions, restricted_contributions, source, retrieved_at)
    VALUES (?, ?, ?, ?, ?, 'github_graphql_api', ?)
    ON CONFLICT(login, year) DO UPDATE SET
        total_contributions=excluded.total_contributions,
        restricted_contributions=excluded.restricted_contributions,
        retrieved_at=excluded.retrieved_at
    """, (github_user_id, clean_login, year, total, restricted, retrieved_at))
    conn.commit()
    conn.close()


def save_repository_contributions(
    login: str,
    github_user_id: Optional[int],
    year: str,
    repos: List[Dict[str, Any]],
    retrieved_at: str
):
    """Save repository-grouped public contributions with provenance."""
    if not repos or not login:
        return
    clean_login = str(login).strip().lower()
    conn = get_db_connection()
    cursor = conn.cursor()
    records = []
    for r in repos:
        records.append((
            github_user_id,
            clean_login,
            year,
            r.get("repository_id", ""),
            r.get("repository_name", ""),
            r.get("url", ""),
            r.get("commit_count", 0),
            1 if r.get("is_private") else 0,
            r.get("primary_language", ""),
            "github_graphql_api",
            retrieved_at
        ))

    cursor.executemany("""
    INSERT INTO github_repository_contributions (
        github_user_id, login, year, repository_id, repository_name, repository_url,
        commit_count, is_private, primary_language, source, retrieved_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(login, year, repository_name) DO UPDATE SET
        commit_count=excluded.commit_count,
        is_private=excluded.is_private,
        primary_language=excluded.primary_language,
        retrieved_at=excluded.retrieved_at
    """, records)

    conn.commit()
    conn.close()


# Auto-initialize DB on import
init_github_db()
