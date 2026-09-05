"""
GitHub GraphQL API Client.
Executes official GraphQL queries for ContributionsCollection, ContributionCalendar,
yearly contribution collections, and commitContributionsByRepository.
"""
import httpx
from typing import Optional, Dict, Any, Tuple
from app.github.oauth_service import get_current_token

GRAPHQL_URL = "https://api.github.com/graphql"

CONTRIBUTION_GRAPHQL_QUERY = """
query($username: String!, $from: DateTime, $to: DateTime) {
  user(login: $username) {
    id
    login
    name
    avatarUrl
    contributionsCollection(from: $from, to: $to) {
      contributionYears
      hasAnyContributions
      hasAnyRestrictedContributions
      restrictedContributionsCount
      totalCommitContributions
      totalIssueContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      totalRepositoriesWithContributedIssues
      totalRepositoriesWithContributedPullRequests
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            contributionLevel
            weekday
          }
        }
        months {
          name
          year
          firstDay
          totalWeeks
        }
      }
      commitContributionsByRepository(maxRepositories: 25) {
        repository {
          name
          nameWithOwner
          url
          isPrivate
          stargazerCount
          primaryLanguage {
            name
            color
          }
        }
        contributions {
          totalCount
        }
      }
    }
  }
}
"""

async def execute_github_graphql(
    query: str,
    variables: Dict[str, Any],
    token: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Execute GraphQL query against GitHub GraphQL API.
    Returns (data, error_reason, status_code_label).
    """
    auth_token = token or get_current_token()
    if not auth_token:
        return None, "GitHub Ownership Not Verified. Connect your GitHub account or provide an access token.", "UNAUTHORIZED"

    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "User-Agent": "AI-Resume-ATS/2.0"
    }

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=headers
            )

            if resp.status_code == 401:
                return None, "GitHub authentication token is invalid or expired. Please re-authenticate.", "UNAUTHORIZED"

            if resp.status_code == 403:
                # Check for rate limit in headers
                remaining = resp.headers.get("x-ratelimit-remaining", "0")
                if remaining == "0":
                    reset_time = resp.headers.get("x-ratelimit-reset", "soon")
                    return None, f"GitHub API Rate Limit Reached. Contribution data cannot currently be retrieved. Rate limit resets at {reset_time}.", "RATE_LIMITED"
                return None, "GitHub API request forbidden: insufficient permissions or organization SSO required.", "FORBIDDEN"

            if resp.status_code != 200:
                return None, f"GitHub API request failed with HTTP {resp.status_code}.", f"HTTP_{resp.status_code}"

            result = resp.json()

            # Inspect GraphQL errors array
            if "errors" in result and result["errors"]:
                err_messages = [e.get("message", "") for e in result["errors"]]
                joined_err = "; ".join(err_messages)

                if any("rate limit" in m.lower() for m in err_messages):
                    return None, "GitHub API Rate Limit Reached. Contribution data cannot currently be retrieved.", "RATE_LIMITED"

                if any("could not resolve to a user" in m.lower() for m in err_messages):
                    return None, f"GitHub Profile Not Found: Candidate account '@{variables.get('username')}' does not exist on GitHub.", "NOT_FOUND"

                return None, f"GitHub GraphQL Error: {joined_err}", "GRAPHQL_ERROR"

            data = result.get("data")
            if not data or not data.get("user"):
                return None, f"GitHub Profile Not Found: No profile data returned for '@{variables.get('username')}'.", "NOT_FOUND"

            return data, None, "SUCCESS"

    except httpx.TimeoutException:
        return None, "GitHub API request timed out. Please try again.", "TIMEOUT"
    except Exception as e:
        return None, f"GitHub API network error: {str(e)}", "NETWORK_ERROR"

async def fetch_user_contributions_graphql(
    username: str,
    year: Optional[int] = None,
    token: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str], Optional[str]]:
    """
    Fetch user contributions collection for a given year or latest 1 year.
    Returns (contributions_collection, error_reason, status_code_label).
    """
    variables: Dict[str, Any] = {"username": username}

    if year:
        # ISO-8601 UTC bounds for specific calendar year
        variables["from"] = f"{year}-01-01T00:00:00Z"
        variables["to"] = f"{year}-12-31T23:59:59Z"

    data, error, status = await execute_github_graphql(CONTRIBUTION_GRAPHQL_QUERY, variables, token=token)
    if error or not data:
        return None, error, status

    user_node = data.get("user", {})
    contributions = user_node.get("contributionsCollection")
    return {
        "user": {
            "id": user_node.get("id"),
            "login": user_node.get("login"),
            "name": user_node.get("name"),
            "avatar_url": user_node.get("avatarUrl")
        },
        "contributions": contributions
    }, None, "SUCCESS"
