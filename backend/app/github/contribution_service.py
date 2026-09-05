"""
GitHub Contribution Processing Service.
Transforms raw GitHub GraphQL ContributionsCollection and ContributionCalendar into
structured, validated data payloads with provenance and SQLite synchronization.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone

from app.github.github_models import (
    ContributionCalendar,
    ContributionWeek,
    ContributionDay,
    ContributionMonth,
    ContributionTypesBreakdown,
    RepositoryContribution,
    GitHubContributionPayload,
    GitHubOwnershipStatus
)
from app.github.graphql_client import fetch_user_contributions_graphql
from app.github.identity_service import check_current_ownership
from app.github.db import save_contribution_days, save_yearly_stats

# Map GitHub GraphQL contribution levels to integers 0..4
LEVEL_MAP = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4
}

def parse_graphql_calendar(raw_calendar: Dict[str, Any]) -> Tuple[ContributionCalendar, List[Dict[str, Any]]]:
    """
    Parse raw GraphQL ContributionCalendar into model and flat list of days.
    """
    total = raw_calendar.get("totalContributions", 0)
    raw_weeks = raw_calendar.get("weeks", [])
    raw_months = raw_calendar.get("months", [])

    weeks_list: List[ContributionWeek] = []
    flat_days: List[Dict[str, Any]] = []

    for w in raw_weeks:
        days_in_week: List[ContributionDay] = []
        for d in w.get("contributionDays", []):
            date_str = d.get("date", "")
            count = d.get("contributionCount", 0)
            lvl_str = d.get("contributionLevel", "NONE")
            lvl_num = LEVEL_MAP.get(str(lvl_str).upper(), 0)
            wday = d.get("weekday", 0)

            # Parse month name and day number
            m_name = None
            day_num = None
            if date_str and len(date_str) >= 10:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    m_name = dt.strftime("%b")
                    day_num = dt.day
                except Exception:
                    pass

            c_day = ContributionDay(
                date=date_str,
                contributionCount=count,
                contributionLevel=str(lvl_num),
                weekday=wday,
                month=m_name,
                day=day_num
            )
            days_in_week.append(c_day)
            flat_days.append({
                "date": date_str,
                "contributionCount": count,
                "contributionLevel": str(lvl_num),
                "weekday": wday
            })
        weeks_list.append(ContributionWeek(contributionDays=days_in_week))

    months_list: List[ContributionMonth] = []
    for m in raw_months:
        months_list.append(ContributionMonth(
            name=m.get("name", ""),
            year=m.get("year", 2026),
            firstDay=m.get("firstDay", ""),
            totalWeeks=m.get("totalWeeks", 4)
        ))

    calendar_model = ContributionCalendar(
        totalContributions=total,
        weeks=weeks_list,
        months=months_list
    )
    return calendar_model, flat_days

def parse_top_repositories(raw_repos: List[Dict[str, Any]]) -> List[RepositoryContribution]:
    """Parse commitContributionsByRepository list."""
    results: List[RepositoryContribution] = []
    for item in raw_repos:
        repo = item.get("repository", {})
        contrib = item.get("contributions", {})
        c_count = contrib.get("totalCount", 0)

        p_lang = repo.get("primaryLanguage") or {}
        lang_name = p_lang.get("name")
        lang_color = p_lang.get("color")

        results.append(RepositoryContribution(
            repository_name=repo.get("nameWithOwner") or repo.get("name", "unknown"),
            url=repo.get("url", ""),
            is_private=repo.get("isPrivate", False),
            commit_count=c_count,
            primary_language=lang_name,
            language_color=lang_color,
            stars=repo.get("stargazerCount", 0)
        ))
    return results

async def get_verified_github_contributions(
    username: str,
    selected_year: Optional[str] = None,
    token: Optional[str] = None
) -> GitHubContributionPayload:
    """
    Fetch, verify, process, and persist real GitHub contribution data.
    Strictly uses official GraphQL API data without any fake or demo generation.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    clean_username = username.strip().lstrip("@")

    # 1. Check Ownership Status
    ownership = await check_current_ownership(resume_username=clean_username)

    # 2. Year selection parsing
    year_int = None
    if selected_year and selected_year.isdigit():
        year_int = int(selected_year)

    # 3. Query GraphQL
    raw_data, error_reason, status_code = await fetch_user_contributions_graphql(
        username=clean_username,
        year=year_int,
        token=token
    )

    if error_reason or not raw_data:
        # Return honest error state without mock fallback
        return GitHubContributionPayload(
            username=clean_username,
            ownership=ownership,
            years_active=[],
            selected_year=selected_year,
            yearly_totals={},
            restricted_totals={},
            has_restricted_contributions=False,
            calendar=None,
            types_breakdown=None,
            top_repositories=[],
            source="github_graphql_api",
            retrieved_at=now_iso,
            data_available=False,
            error_reason=error_reason or "GitHub contribution data could not be retrieved."
        )

    user_info = raw_data.get("user", {})
    contrib_col = raw_data.get("contributions", {})

    # Extract active contribution years
    years_active = [str(y) for y in contrib_col.get("contributionYears", [])]
    current_year_str = str(year_int) if year_int else (years_active[0] if years_active else "2026")

    # Parse Calendar
    raw_calendar = contrib_col.get("contributionCalendar", {})
    calendar_model, flat_days = parse_graphql_calendar(raw_calendar)

    # Breakdown of types
    breakdown = ContributionTypesBreakdown(
        commits=contrib_col.get("totalCommitContributions", 0),
        pull_requests=contrib_col.get("totalPullRequestContributions", 0),
        issues=contrib_col.get("totalIssueContributions", 0),
        reviews=contrib_col.get("totalPullRequestReviewContributions", 0),
        discussions=0,
        repositories_contributed=(
            contrib_col.get("totalRepositoriesWithContributedCommits", 0) +
            contrib_col.get("totalRepositoriesWithContributedPullRequests", 0)
        )
    )

    # Parse top repositories
    raw_repo_contribs = contrib_col.get("commitContributionsByRepository", [])
    top_repos = parse_top_repositories(raw_repo_contribs)

    # Restricted contributions
    has_restricted = contrib_col.get("hasAnyRestrictedContributions", False)
    restricted_count = contrib_col.get("restrictedContributionsCount", 0)

    # Synchronize with SQLite provenance DB
    gh_user_id = user_info.get("id")
    save_contribution_days(
        login=clean_username,
        github_user_id=None,
        days=flat_days,
        retrieved_at=now_iso
    )
    save_yearly_stats(
        login=clean_username,
        github_user_id=None,
        year=current_year_str,
        total=calendar_model.totalContributions,
        restricted=restricted_count,
        retrieved_at=now_iso
    )

    yearly_totals = {current_year_str: calendar_model.totalContributions}
    restricted_totals = {current_year_str: restricted_count}

    return GitHubContributionPayload(
        username=clean_username,
        ownership=ownership,
        years_active=years_active,
        selected_year=current_year_str,
        yearly_totals=yearly_totals,
        restricted_totals=restricted_totals,
        has_restricted_contributions=has_restricted,
        calendar=calendar_model,
        types_breakdown=breakdown,
        top_repositories=top_repos,
        source="github_graphql_api",
        retrieved_at=now_iso,
        data_available=True,
        error_reason=None
    )
