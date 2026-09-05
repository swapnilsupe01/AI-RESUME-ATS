"""
GitHub Repository Activity & Evidence Service.
Formats repository-grouped contribution evidence, emphasizes development rigor
and activity evidence over raw commit counts, and handles public/private visibility.
"""
from typing import List, Dict, Any
from app.github.github_models import RepositoryContribution

def format_repository_evidence(
    repos: List[RepositoryContribution],
    has_restricted: bool = False
) -> Dict[str, Any]:
    """
    Format repository evidence ensuring transparency and avoiding superficial quality assumptions.
    Rule 9: Never confuse commit count with contribution quality.
    Rule 16: Clearly distinguish public vs private/restricted contributions.
    """
    total_commits = sum(r.commit_count for r in repos)
    public_repos = [r for r in repos if not r.is_private]
    private_repos = [r for r in repos if r.is_private]

    evidence_summary = []
    for r in repos[:10]:
        evidence_summary.append({
            "repo_name": r.repository_name,
            "url": r.url,
            "commits": r.commit_count,
            "is_private": r.is_private,
            "language": r.primary_language or "General",
            "evidence_type": "Public Repository Activity" if not r.is_private else "Restricted / Private Repository Activity",
            "note": "Candidate recorded direct commit participation"
        })

    visibility_notes = []
    if has_restricted:
        visibility_notes.append("Candidate has anonymized/restricted private contribution activity enabled on GitHub.")
    if private_repos:
        visibility_notes.append(f"{len(private_repos)} private repositories included in contribution count.")
    else:
        visibility_notes.append("Private contribution details are not available via public scope.")

    return {
        "total_repositories": len(repos),
        "total_commits": total_commits,
        "repositories": [r.dict() for r in repos],
        "top_evidence": evidence_summary,
        "visibility_notes": visibility_notes,
        "evaluation_guidance": (
            "Recruiter Notice: Commit count alone does not establish engineering quality. "
            "Examine repository structure, test coverage, code architecture, and pull request activity "
            "for verified technical competency."
        )
    }
