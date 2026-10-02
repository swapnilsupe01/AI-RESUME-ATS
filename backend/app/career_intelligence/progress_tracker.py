"""
Enhanced Progress Tracker for Layer F — AI Career Intelligence Engine.
Tracks multi-event learning activity, milestone completions, interview attempts,
skill verifications, and progress analytics — without automated quiz grading.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# In-memory store. Will be replaced by a persistent database in Phase 2.
_PROGRESS: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
_MILESTONES: Dict[str, Dict[str, Any]] = {}  # session_id -> milestone metadata


EVENT_TYPES = {
    "assessment_started", "assessment_submitted",
    "interview_answered", "interview_started",
    "resource_opened", "task_completed",
    "skill_verified", "milestone_completed",
    "roadmap_generated", "gap_analysis_run",
    "career_analyze_full_run"
}


def new_session() -> str:
    """Create and return a new unique session ID."""
    return str(uuid.uuid4())


def record_event(session_id: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Record a learning or career intelligence event for a session.
    """
    if event_type not in EVENT_TYPES:
        # Accept unknown events but tag them
        payload["_unknown_event_type"] = True

    event: Dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _PROGRESS[session_id].append(event)
    return event


def complete_milestone(session_id: str, skill: str, milestone_text: str) -> Dict[str, Any]:
    """Mark a specific roadmap milestone as completed for a skill."""
    return record_event(
        session_id,
        "milestone_completed",
        {"skill": skill, "milestone": milestone_text}
    )


def verify_skill(session_id: str, skill: str, evidence_url: str = "", notes: str = "") -> Dict[str, Any]:
    """Mark a skill as independently verified with optional evidence link."""
    return record_event(
        session_id,
        "skill_verified",
        {"skill": skill, "evidence_url": evidence_url, "notes": notes}
    )


def record_resource_opened(session_id: str, resource_id: str, skill: str, title: str) -> Dict[str, Any]:
    """Log that a learning resource was accessed."""
    return record_event(
        session_id,
        "resource_opened",
        {"resource_id": resource_id, "skill": skill, "title": title}
    )


def get_progress(session_id: str) -> Dict[str, Any]:
    """
    Retrieve aggregated progress analytics for a session.
    """
    events: List[Dict[str, Any]] = _PROGRESS.get(session_id, [])

    # Aggregate assessment scores
    assessment_scores = [
        e["payload"].get("overall_score")
        for e in events
        if e["event_type"] == "assessment_submitted"
        and "overall_score" in e["payload"]
    ]

    # Interview scores
    interview_scores = [
        e["payload"].get("score")
        for e in events
        if e["event_type"] == "interview_answered"
        and "score" in e["payload"]
    ]

    # Completed milestones
    milestones_completed = [
        {"skill": e["payload"].get("skill"), "milestone": e["payload"].get("milestone"), "timestamp": e["timestamp"]}
        for e in events
        if e["event_type"] == "milestone_completed"
    ]

    # Verified skills
    verified_skills = [
        {"skill": e["payload"].get("skill"), "evidence": e["payload"].get("evidence_url"), "timestamp": e["timestamp"]}
        for e in events
        if e["event_type"] == "skill_verified"
    ]

    # Resources opened (unique)
    resources_opened: List[str] = list({
        e["payload"].get("resource_id")
        for e in events
        if e["event_type"] == "resource_opened" and e["payload"].get("resource_id")
    })

    # Event type counts
    event_type_counts: Dict[str, int] = defaultdict(int)
    for e in events:
        event_type_counts[e["event_type"]] += 1

    avg_assessment = round(sum(assessment_scores) / len(assessment_scores), 1) if assessment_scores else None
    avg_interview = round(sum(interview_scores) / len(interview_scores), 1) if interview_scores else None

    return {
        "session_id": session_id,
        "event_count": len(events),
        "event_type_counts": dict(event_type_counts),
        "events": events,
        "assessment_scores": assessment_scores,
        "latest_assessment_score": assessment_scores[-1] if assessment_scores else None,
        "average_assessment_score": avg_assessment,
        "interview_scores": interview_scores,
        "average_interview_score": avg_interview,
        "milestones_completed": milestones_completed,
        "verified_skills": verified_skills,
        "unique_resources_opened": resources_opened,
        "progress_summary": {
            "milestones_completed_count": len(milestones_completed),
            "skills_verified_count": len(verified_skills),
            "resources_opened_count": len(resources_opened),
            "total_assessments": len(assessment_scores),
            "total_interview_answers": len(interview_scores),
        },
        "note": (
            "Progress is tracked per session. "
            "Verified skills require manual confirmation or linked evidence. "
            "Interview scores are keyword-heuristic estimates, not ground truth."
        ),
    }


def clear_session(session_id: str) -> None:
    """Remove all events for a session (e.g. for testing or resets)."""
    if session_id in _PROGRESS:
        del _PROGRESS[session_id]
