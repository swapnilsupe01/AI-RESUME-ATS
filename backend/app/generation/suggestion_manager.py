"""
Suggestion Manager — Layer E AI Resume Upgrade Engine.

Manages an in-memory session of structured resume improvement suggestions.
Each session is keyed by a unique session_id. Sessions are isolated and
do not share data across users or requests.

Limitations (demo scope):
  - Sessions are stored in-memory (process lifetime only).
  - Sessions expire after SESSION_TTL_SECONDS of inactivity.
  - In production, replace the in-memory dict with a database or
    encrypted cache tied to the user's authenticated session.
  - Do not store session data longer than necessary.
"""

import time
import uuid
import copy
from typing import Dict, List, Optional, Any

from app.generation.preservation_validator import (
    sanitize_ai_text,
    contains_ai_leakage,
    validate_and_preserve,
)

# Session time-to-live: 2 hours of inactivity
SESSION_TTL_SECONDS = 7200


class Suggestion:
    """
    Represents a single AI-generated improvement suggestion for one
    section of the resume.
    """

    def __init__(
        self,
        section: str,
        item_id: str,
        field: str,
        original_text: str,
        suggested_text: str,
        explanation: str,
        jd_requirement: str = "",
        evidence_status: str = "pending_review",
        evidence_note: str = "",
    ):
        self.id: str = f"sug_{uuid.uuid4().hex[:10]}"
        self.section: str = section                 # e.g. "summary", "experience", "project"
        self.item_id: str = item_id                 # ID of ExperienceItem or ProjectItem
        self.field: str = field                     # e.g. "highlights[0]", "description", "summary"
        self.original_text: str = original_text
        self.suggested_text: str = sanitize_ai_text(suggested_text)
        self.explanation: str = explanation
        self.jd_requirement: str = jd_requirement   # Which JD requirement this addresses
        self.evidence_status: str = evidence_status  # "supported" | "needs_confirmation" | "unsupported"
        self.evidence_note: str = evidence_note
        self.status: str = "pending"                 # "pending" | "accepted" | "rejected"
        self.edited_text: str = ""                   # User's manual override

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section": self.section,
            "item_id": self.item_id,
            "field": self.field,
            "original_text": self.original_text,
            "suggested_text": self.suggested_text,
            "explanation": self.explanation,
            "jd_requirement": self.jd_requirement,
            "evidence_status": self.evidence_status,
            "evidence_note": self.evidence_note,
            "status": self.status,
            "edited_text": self.edited_text,
            # Resolved text = edited if set and accepted, else suggested if accepted, else original
            "resolved_text": self._resolved_text(),
        }

    def _resolved_text(self) -> str:
        if self.status == "accepted":
            return self.edited_text if self.edited_text.strip() else self.suggested_text
        return self.original_text


class UpgradeSession:
    """
    Container for a single user's upgrade session.
    Stores the canonical resume, suggestions, and the original resume snapshot.
    """

    def __init__(self, canonical_resume: Dict[str, Any], session_id: str):
        self.session_id = session_id
        self.original_canonical = copy.deepcopy(canonical_resume)
        self.current_canonical = copy.deepcopy(canonical_resume)
        self.suggestions: List[Suggestion] = []
        self.created_at = time.time()
        self.last_accessed = time.time()

    def touch(self):
        self.last_accessed = time.time()

    def add_suggestion(self, suggestion: Suggestion):
        self.suggestions.append(suggestion)

    def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        return next((s for s in self.suggestions if s.id == suggestion_id), None)

    def accept(self, suggestion_id: str, edited_text: str = "") -> bool:
        s = self.get_suggestion(suggestion_id)
        if not s:
            return False
        s.status = "accepted"
        s.edited_text = sanitize_ai_text(edited_text).strip()
        return True

    def reject(self, suggestion_id: str) -> bool:
        s = self.get_suggestion(suggestion_id)
        if not s:
            return False
        s.status = "rejected"
        return True

    def pending_count(self) -> int:
        return sum(1 for s in self.suggestions if s.status == "pending")

    def accepted_count(self) -> int:
        return sum(1 for s in self.suggestions if s.status == "accepted")

    def rejected_count(self) -> int:
        return sum(1 for s in self.suggestions if s.status == "rejected")

    def build_approved_resume(self) -> Dict[str, Any]:
        """
        Return a deep copy of the canonical resume with ONLY accepted suggestions applied.
        Pending and rejected suggestions are NOT included in the output.
        Enforces zero data loss preservation validation.
        """
        approved = copy.deepcopy(self.original_canonical)

        # Apply accepted suggestions
        for s in self.suggestions:
            if s.status != "accepted":
                continue
            resolved = s._resolved_text()
            self._apply_to_resume(approved, s, resolved)

        # Validate that no factual data was lost and strip any AI commentary
        validated, warnings = validate_and_preserve(self.original_canonical, approved)
        if warnings:
            logger.info("[UpgradeSession] Preservation validation notes: %s", warnings)

        return validated

    def _apply_to_resume(
        self,
        resume: Dict[str, Any],
        suggestion: Suggestion,
        resolved_text: str,
    ):
        """Apply a single accepted suggestion to the resume dict in-place."""
        section = suggestion.section
        item_id = suggestion.item_id
        field = suggestion.field

        if section == "summary":
            resume["summary"] = resolved_text
            if isinstance(resume.get("profile"), dict):
                resume["profile"]["summary"] = resolved_text
            return

        if section == "experience":
            for exp in resume.get("experience", []):
                if exp.get("id") == item_id:
                    if field.startswith("highlights["):
                        try:
                            idx = int(field.split("[")[1].rstrip("]"))
                            highlights = exp.get("highlights", [])
                            if idx < len(highlights):
                                highlights[idx] = resolved_text
                        except (ValueError, IndexError):
                            pass
                    break
            return

        if section == "project":
            if field == "order":
                # Reorder projects list based on resolved text
                current_projects = resume.get("projects", [])
                if not current_projects or len(current_projects) <= 1:
                    return

                proj_by_name = {}
                for p in current_projects:
                    p_name = str(p.get("name") or p.get("title") or "").strip().lower()
                    if p_name:
                        proj_by_name[p_name] = p

                reordered = []
                used_ids = set()

                import re
                for line in resolved_text.splitlines():
                    line_clean = re.sub(r"^\d+\.\s*", "", line).split("—")[0].split("-")[0].split("[")[0].strip().lower()
                    if not line_clean:
                        continue
                    for p_name, p in proj_by_name.items():
                        p_uid = str(p.get("id") or id(p))
                        if p_uid not in used_ids and (p_name in line_clean or line_clean in p_name):
                            reordered.append(p)
                            used_ids.add(p_uid)
                            break

                for p in current_projects:
                    p_uid = str(p.get("id") or id(p))
                    if p_uid not in used_ids:
                        reordered.append(p)

                resume["projects"] = reordered
                return

            for proj in resume.get("projects", []):
                if proj.get("id") == item_id:
                    if field == "description":
                        proj["description"] = resolved_text
                    elif field.startswith("highlights["):
                        try:
                            idx = int(field.split("[")[1].rstrip("]"))
                            highlights = proj.get("highlights", [])
                            if idx < len(highlights):
                                highlights[idx] = resolved_text
                        except (ValueError, IndexError):
                            pass
                    break
            return

    def summary_stats(self) -> Dict[str, int]:
        by_evidence = {"supported": 0, "needs_confirmation": 0, "unsupported": 0}
        for s in self.suggestions:
            key = s.evidence_status
            if key in by_evidence:
                by_evidence[key] += 1
        return {
            "total": len(self.suggestions),
            "pending": self.pending_count(),
            "accepted": self.accepted_count(),
            "rejected": self.rejected_count(),
            **by_evidence,
        }


# ── Global session store ─────────────────────────────────────────────────────

_sessions: Dict[str, UpgradeSession] = {}


def create_session(canonical_resume: Dict[str, Any]) -> str:
    """Create a new upgrade session and return its ID."""
    _evict_expired()
    session_id = f"sess_{uuid.uuid4().hex}"
    _sessions[session_id] = UpgradeSession(canonical_resume, session_id)
    return session_id


def get_session(session_id: str) -> Optional[UpgradeSession]:
    """Return session if it exists and is not expired. Touches last-access time."""
    session = _sessions.get(session_id)
    if session is None:
        return None
    if time.time() - session.last_accessed > SESSION_TTL_SECONDS:
        del _sessions[session_id]
        return None
    session.touch()
    return session


def delete_session(session_id: str):
    _sessions.pop(session_id, None)


def _evict_expired():
    """Remove sessions that have been inactive beyond SESSION_TTL_SECONDS."""
    now = time.time()
    expired = [
        sid for sid, s in _sessions.items()
        if now - s.last_accessed > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        del _sessions[sid]
