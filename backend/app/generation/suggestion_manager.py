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
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

from app.generation.preservation_validator import (
    sanitize_ai_text,
    contains_ai_leakage,
    validate_and_preserve,
)

# Session time-to-live: 30 minutes of inactivity
SESSION_TTL_SECONDS = 1800


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
        category: str = "OTHER",
        validation_status: str = "valid",
    ):
        self.id: str = f"sug_{uuid.uuid4().hex[:10]}"
        self.section: str = section                 # e.g. "summary", "experience", "project"
        self.item_id: str = item_id                 # ID of ExperienceItem or ProjectItem
        self.field: str = field                     # e.g. "highlights[0]", "description", "summary"
        self.category: str = category               # e.g. "TECH_STACK", "PROJECT_DESCRIPTION", "ACHIEVEMENT"
        self.original_text: str = original_text
        self.suggested_text: str = sanitize_ai_text(suggested_text)
        self.explanation: str = explanation
        self.jd_requirement: str = jd_requirement   # Which JD requirement this addresses
        self.evidence_status: str = evidence_status  # "supported" | "needs_confirmation" | "unsupported"
        self.evidence_note: str = evidence_note
        self.status: str = "pending"                 # "pending" | "accepted" | "rejected"
        self.edited_text: str = ""                   # User's manual override
        self.validation_status: str = validation_status # "valid" | "preserved_original" | "fallback_applied"

    @property
    def suggestion_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "section": self.section,
            "item_id": self.item_id,
            "field": self.field,
            "category": self.category,
            "content_type": self.category,
            "original_text": self.original_text,
            "suggested_text": self.suggested_text,
            "explanation": self.explanation,
            "jd_requirement": self.jd_requirement,
            "evidence_status": self.evidence_status,
            "evidence_note": self.evidence_note,
            "status": self.status,
            "edited_text": self.edited_text,
            "custom_override": self.edited_text,
            "validation_status": self.validation_status,
            # Resolved text = edited if set and accepted, else suggested if accepted, else original
            "resolved_text": self._resolved_text(),
            "accepted_text": self._resolved_text() if self.status == "accepted" else "",
        }

    def _resolved_text(self) -> str:
        if self.status == "accepted":
            if self.edited_text.strip():
                return self.edited_text.strip()
            if self.evidence_status == "supported" or getattr(self, "confirmed", False):
                return self.suggested_text
            return self.original_text
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
        self.suggested_skills_to_verify: List[str] = []
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

    def accept_suggestion(self, suggestion_id: str, edited_text: str = "", custom_edit: str = "") -> bool:
        override = custom_edit or edited_text
        return self.accept(suggestion_id, override)

    def reject_suggestion(self, suggestion_id: str) -> bool:
        return self.reject(suggestion_id)

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
        """Apply a single accepted suggestion to the resume dict in-place at the exact position."""
        section = suggestion.section
        item_id = suggestion.item_id
        field = suggestion.field
        orig_text = suggestion.original_text.strip() if suggestion.original_text else ""

        if section == "summary":
            resume["summary"] = resolved_text
            if isinstance(resume.get("profile"), dict):
                resume["profile"]["summary"] = resolved_text
            return

        if section == "experience":
            for e_idx, exp in enumerate(resume.get("experience", [])):
                e_uid = exp.get("id") or f"exp_{e_idx}"
                hl_list = exp.get("highlights") if isinstance(exp.get("highlights"), list) else None
                bl_list = exp.get("bullets") if isinstance(exp.get("bullets"), list) else None
                id_matches = (e_uid == item_id or exp.get("id") == item_id)
                contains_orig = bool(
                    orig_text and (
                        (hl_list and any(orig_text in h for h in hl_list))
                        or (bl_list and any(orig_text in b for b in bl_list))
                    )
                )

                if id_matches or contains_orig:
                    if field.startswith("highlights["):
                        try:
                            target_idx = int(field.split("[")[1].rstrip("]"))
                        except (ValueError, IndexError):
                            target_idx = -1

                        def _replace_in_exp_list(lst: List[str]):
                            if not lst:
                                return
                            if 0 <= target_idx < len(lst) and (not orig_text or lst[target_idx].strip() == orig_text):
                                lst[target_idx] = resolved_text
                                return
                            if orig_text:
                                for i, item in enumerate(lst):
                                    if item.strip() == orig_text:
                                        lst[i] = resolved_text
                                        return
                            if 0 <= target_idx < len(lst):
                                lst[target_idx] = resolved_text

                        if hl_list is not None:
                            _replace_in_exp_list(hl_list)
                        if bl_list is not None:
                            _replace_in_exp_list(bl_list)
                        if hl_list is None and bl_list is None:
                            exp["highlights"] = [resolved_text]
                    elif field == "description":
                        exp["description"] = resolved_text
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
                    line_clean = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
                    tokens = [p.strip().lower() for p in re.split(r"\s*[—–\-–\[]\s*", line_clean) if p.strip()]
                    if not tokens:
                        continue
                    first_tok = tokens[0]
                    matched_p = None
                    for p_name, p in proj_by_name.items():
                        p_uid = str(p.get("id") or id(p))
                        if p_uid in used_ids:
                            continue
                        if p_name in first_tok or first_tok in p_name or any(p_name in tok or tok in p_name for tok in tokens):
                            matched_p = p
                            used_ids.add(p_uid)
                            break
                        p_words = [w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", p_name)]
                        if p_words and sum(1 for w in p_words if w in line_clean.lower()) >= len(p_words):
                            matched_p = p
                            used_ids.add(p_uid)
                            break
                    if matched_p:
                        reordered.append(matched_p)

                for p in current_projects:
                    p_uid = str(p.get("id") or id(p))
                    if p_uid not in used_ids:
                        reordered.append(p)

                resume["projects"] = reordered
                return

            for p_idx, proj in enumerate(resume.get("projects", [])):
                p_uid = proj.get("id") or f"proj_{p_idx}"
                hl_list = proj.get("highlights") if isinstance(proj.get("highlights"), list) else None
                bl_list = proj.get("bullets") if isinstance(proj.get("bullets"), list) else None
                desc = proj.get("description", "")
                id_matches = (p_uid == item_id or proj.get("id") == item_id)
                contains_orig = bool(
                    orig_text and (
                        (hl_list and any(orig_text in h for h in hl_list))
                        or (bl_list and any(orig_text in b for b in bl_list))
                        or (field == "description" and desc.strip() == orig_text)
                    )
                )

                if id_matches or contains_orig:
                    if field == "description":
                        proj["description"] = resolved_text
                    elif field.startswith("highlights["):
                        try:
                            target_idx = int(field.split("[")[1].rstrip("]"))
                        except (ValueError, IndexError):
                            target_idx = -1

                        def _replace_in_proj_list(lst: List[str]):
                            if not lst:
                                return
                            if 0 <= target_idx < len(lst) and (not orig_text or lst[target_idx].strip() == orig_text):
                                lst[target_idx] = resolved_text
                                return
                            if orig_text:
                                for i, item in enumerate(lst):
                                    if item.strip() == orig_text:
                                        lst[i] = resolved_text
                                        return
                            if 0 <= target_idx < len(lst):
                                lst[target_idx] = resolved_text

                        if hl_list is not None:
                            _replace_in_proj_list(hl_list)
                        if bl_list is not None:
                            _replace_in_proj_list(bl_list)
                        if hl_list is None and bl_list is None:
                            proj["highlights"] = [resolved_text]
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


class SessionId(str):
    """A string subclass representing session_id, also exposing UpgradeSession methods."""
    def __new__(cls, session_id: str, session: 'UpgradeSession'):
        inst = super().__new__(cls, session_id)
        inst._session = session
        return inst

    def __getattr__(self, name):
        return getattr(self._session, name)


def create_session(arg1: Any, arg2: Optional[Any] = None) -> SessionId:
    """Create a new upgrade session and return its ID (which also proxies to the session object)."""
    _evict_expired()
    if arg2 is not None:
        if isinstance(arg1, str):
            session_id = arg1
            canonical_resume = arg2
        else:
            canonical_resume = arg1
            session_id = str(arg2)
    else:
        canonical_resume = arg1
        session_id = f"sess_{uuid.uuid4().hex}"

    session = UpgradeSession(canonical_resume, session_id)
    _sessions[session_id] = session
    return SessionId(session_id, session)


def get_session(session_id: str) -> Optional[UpgradeSession]:
    """Return session if it exists and is not expired. Touches last-access time. Strictly keyed by session_id, no 'latest' fallback."""
    if not session_id or not isinstance(session_id, str):
        return None
    session = _sessions.get(session_id.strip())
    if session is None:
        return None
    if time.time() - session.last_accessed > SESSION_TTL_SECONDS:
        del _sessions[session_id.strip()]
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


# Alias for backward compatibility
SuggestionSession = UpgradeSession
