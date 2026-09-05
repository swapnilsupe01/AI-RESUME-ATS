"""
GitHub Intelligence Pydantic Models.
Defines schemas for ownership verification, contributions collection,
contribution calendar days, yearly stats, and repository activity.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ContributionDay(BaseModel):
    date: str
    contributionCount: int
    contributionLevel: str  # "NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"
    weekday: int  # 0 = Mon, 6 = Sun
    month: Optional[str] = None
    day: Optional[int] = None

class ContributionWeek(BaseModel):
    contributionDays: List[ContributionDay]

class ContributionMonth(BaseModel):
    name: str
    year: int
    firstDay: str
    totalWeeks: int

class ContributionCalendar(BaseModel):
    totalContributions: int
    weeks: List[ContributionWeek]
    months: List[ContributionMonth]

class ContributionTypesBreakdown(BaseModel):
    commits: int = 0
    pull_requests: int = 0
    issues: int = 0
    reviews: int = 0
    discussions: int = 0
    repositories_contributed: int = 0

class RepositoryContribution(BaseModel):
    repository_name: str
    url: str
    is_private: bool = False
    commit_count: int = 0
    primary_language: Optional[str] = None
    language_color: Optional[str] = None
    stars: int = 0

class GitHubOwnershipStatus(BaseModel):
    verified: bool = False
    status: str = "UNVERIFIED"  # "VERIFIED", "MISMATCH", "UNVERIFIED", "NOT_FOUND", "ERROR"
    login: Optional[str] = None
    github_user_id: Optional[int] = None
    avatar_url: Optional[str] = None
    resume_username: Optional[str] = None
    matched: bool = False
    verified_at: Optional[str] = None
    message: str = "GitHub Ownership Not Verified. Connect your GitHub account to retrieve verified contribution data."

class YearlyContributionSummary(BaseModel):
    year: str
    total_contributions: int
    restricted_contributions_count: int = 0
    has_restricted: bool = False

class GitHubContributionPayload(BaseModel):
    username: str
    ownership: GitHubOwnershipStatus
    years_active: List[str] = []
    selected_year: Optional[str] = None
    yearly_totals: Dict[str, int] = {}
    restricted_totals: Dict[str, int] = {}
    has_restricted_contributions: bool = False
    calendar: Optional[ContributionCalendar] = None
    types_breakdown: Optional[ContributionTypesBreakdown] = None
    top_repositories: List[RepositoryContribution] = []
    source: str = "github_graphql_api"
    retrieved_at: str
    data_available: bool = True
    error_reason: Optional[str] = None
