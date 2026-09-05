"""
GitHub Synchronized Provenance Database Manager.
Stores synchronized GitHub contribution and account records in SQLite
with strict provenance fields: source="github_graphql_api" and retrieved_at.
"""
import os
import sqlite3
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "github_provenance.db")

def get_db_connection() -> sqlite3.Connection:
    """Get SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_github_db():
    """Initialize SQLite database tables for verified GitHub evidence."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. github_accounts
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS github_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        github_user_id INTEGER UNIQUE,
        login TEXT NOT NULL,
        profile_url TEXT NOT NULL,
        ownership_verified BOOLEAN NOT NULL DEFAULT 0,
        verified_at TEXT,
        created_at TEXT NOT NULL
    )
    """)

    # 2. github_contributions
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

    # 3. github_yearly_stats
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

    # 4. github_repository_contributions
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

def save_verified_account(
    github_user_id: int,
    login: str,
    profile_url: str,
    ownership_verified: bool,
    verified_at: Optional[str] = None
):
    """Upsert verified GitHub account record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    verified_at_val = verified_at or now_iso

    cursor.execute("""
    INSERT INTO github_accounts (github_user_id, login, profile_url, ownership_verified, verified_at, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(github_user_id) DO UPDATE SET
        login=excluded.login,
        profile_url=excluded.profile_url,
        ownership_verified=excluded.ownership_verified,
        verified_at=excluded.verified_at
    """, (github_user_id, login, profile_url, 1 if ownership_verified else 0, verified_at_val, now_iso))

    conn.commit()
    conn.close()

def get_verified_account(login: str) -> Optional[Dict[str, Any]]:
    """Retrieve verified GitHub account by login."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM github_accounts WHERE LOWER(login) = LOWER(?)", (login,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_contribution_days(login: str, github_user_id: Optional[int], days: List[Dict[str, Any]], retrieved_at: str):
    """Save batch of daily contribution records with source and timestamp provenance."""
    if not days:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    records = []
    for d in days:
        date_str = d.get("date")
        year_str = date_str[:4] if date_str and len(date_str) >= 4 else "2026"
        records.append((
            github_user_id,
            login,
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
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO github_yearly_stats (github_user_id, login, year, total_contributions, restricted_contributions, source, retrieved_at)
    VALUES (?, ?, ?, ?, ?, 'github_graphql_api', ?)
    ON CONFLICT(login, year) DO UPDATE SET
        total_contributions=excluded.total_contributions,
        restricted_contributions=excluded.restricted_contributions,
        retrieved_at=excluded.retrieved_at
    """, (github_user_id, login, year, total, restricted, retrieved_at))
    conn.commit()
    conn.close()

def save_repository_contributions(
    login: str,
    github_user_id: Optional[int],
    year: str,
    repos: List[Dict[str, Any]],
    retrieved_at: str
):
    """Save repository-grouped contributions with provenance."""
    if not repos:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    records = []
    for r in repos:
        records.append((
            github_user_id,
            login,
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
