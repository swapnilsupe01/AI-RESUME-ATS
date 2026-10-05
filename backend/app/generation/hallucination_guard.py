"""
Hallucination Guard — Layer E AI Resume Upgrade Engine.

Validates AI-generated resume suggestions against the candidate's original
resume content to prevent fabricated claims from reaching the user's document.

Rules:
  1. New numbers, percentages, metrics, and scale claims → needs_confirmation
  2. New technology / tool names not in original → unsupported
  3. New business-impact language (revenue, cost savings, team sizes) → needs_confirmation
  4. New credential, certification, or degree claims → unsupported
  5. Wording improvements with no new facts → supported
  6. Original factual content preserved → supported

All checks compare the SUGGESTED text against the ORIGINAL text.
The guard never modifies suggestions; it only assigns an evidence status.
"""

import re
from typing import Tuple, List, Set

# Patterns that signal potentially fabricated metric claims
_METRIC_PATTERNS = [
    r"\b\d+\s*%",                          # percentages: 35%, 40 %
    r"\b\d+\s*[xX]\b",                     # multiples: 3x, 5X
    r"\$\s*\d+",                           # dollar amounts
    r"\b\d+\s*(million|billion|thousand|k\b)", # large figures
    r"\b\d+\s*(users|customers|clients|requests|transactions|queries|employees|engineers|developers|teams?)", # scale claims
    r"\b\d+\s*(ms|milliseconds?|seconds?|minutes?|hours?)", # latency
    r"\breduced?\s+by\s+\d+",             # "reduced by N"
    r"\bincreased?\s+by\s+\d+",           # "increased by N"
    r"\bimproved?\s+by\s+\d+",            # "improved by N"
    r"\bsaving?\s+\$?\d+",               # "saving $X"
    r"\b(top|top-\d+%|ranked\s+#?\d+)",   # ranking claims
]

# Business-impact language that could be fabricated
_IMPACT_PHRASES = [
    r"\brevenue\b", r"\bcost\s+saving", r"\bROI\b", r"\bP&L\b",
    r"\bprofit\b", r"\bcustomer\s+acquisition\b", r"\bchurn\b",
    r"\bSLA\b", r"\buptime\b", r"\b99\.?\d+%\b",
]

# Credential / certification language
_CREDENTIAL_PATTERNS = [
    r"\b(AWS|GCP|Azure|CKA|CKAD|PMP|CISSP|CISA|CEH|TOGAF|SAFe|ISO|ITIL)\b",
    r"\bcertif(ied|ication|icate)\b",
    r"\bpat?ent\b",
    r"\bpublished\b",
    r"\bdegree\b",
    r"\bph\.?d\b",
    r"\bmaster'?s?\b",
    r"\bbachelor'?s?\b",
]


def _extract_numbers(text: str) -> Set[str]:
    """Extract all digit sequences from text for comparison."""
    return set(re.findall(r"\d+(?:\.\d+)?", text))


_COMMON_RESUME_WORDS = {
    "architected", "engineered", "developed", "designed", "built", "implemented",
    "created", "deployed", "maintained", "delivered", "managed", "led", "optimized",
    "collaborated", "spearheaded", "automated", "formulated", "accelerated",
    "executed", "streamlined", "enhanced", "produced", "resolved", "utilized", "utilizing",
    "configured", "analyzed", "integrated", "monitored", "wrote", "authored",
    "orchestrated", "established", "facilitated", "championed", "oversaw",
    "directed", "transformed", "scaled", "modernized", "migrated", "refactored",
    "leveraged", "leveraging", "simulated", "enabling", "streamlining", "identifying",
    "backend", "frontend", "fullstack", "software", "engineer", "developer",
    "components", "services", "applications", "systems", "solutions", "pipeline",
    "pipelines", "infrastructure", "features", "performance", "high-performance",
    "scalable", "robust", "distributed", "production", "enterprise", "cloud",
    "internal", "external", "cross-functional", "end-to-end", "real-time",
    "engine", "platform", "project", "projects", "overview", "description",
    "analysis", "gap", "framework", "language", "model", "process", "processes",
    "clients", "users", "data", "security", "response", "incident", "scanning",
    "threat", "vulnerability", "vulnerabilities", "measures", "predictive",
    "proactive", "sentence", "transformers", "here", "there", "this", "these", "those",
    "rewritten", "improved", "suggested", "updated", "juice", "shop", "iso", "audit",
    "cybersecurity", "orchestration", "threats", "scenarios", "interface",
    "ai-powered", "python-based", "cloud-native", "full-stack", "fastapi-based",
}


def _clean_term(term: str) -> str:
    """Strip common compound adjective suffixes like -based, -powered, -driven."""
    return re.sub(r'-(?:based|powered|driven|enabled|native|centric|oriented)$', '', term, flags=re.IGNORECASE).strip()


def _extract_tech_terms(text: str) -> Set[str]:
    """Extract potential technology/tool names (capitalized words and acronyms)."""
    # Match: CamelCase, ALL_CAPS, multi-word with dots/plus (e.g., C++, Node.js)
    raw_words = re.findall(r"\b[A-Z][a-zA-Z0-9\.\+\#\-]*[a-zA-Z0-9]\b|\b[A-Z]{2,}\b", text)
    stop_caps = {
        "I", "A", "AN", "THE", "AND", "OR", "BUT", "FOR", "IN", "ON", "AT", "TO",
        "BY", "AS", "IS", "ARE", "WAS", "WERE", "BE", "BEEN", "BEING",
        "HAVE", "HAS", "HAD", "DO", "DOES", "DID", "WILL", "WOULD",
        "COULD", "SHOULD", "MAY", "MIGHT", "SHALL", "CAN", "NOT", "NO",
        "SO", "YET", "NOR", "FOR", "US", "WE", "IT", "THEY", "HE", "SHE",
        "HERE", "THERE", "THIS", "THAT", "THESE", "THOSE", "WHAT", "WHEN",
        "WHERE", "WHICH", "WHO", "WHY", "HOW", "NEW", "KEY", "ALL",
        "API", "APIS", "REST", "SDK", "UI", "UX", "AI", "ML", "LLM",
        "ISO", "OWASP", "JUICE", "SHOP", "ENGINE", "PLATFORM", "AUDIT", "GAP",
    }
    result = set()
    for w in raw_words:
        cleaned_w = _clean_term(w)
        if not cleaned_w or cleaned_w.upper() in stop_caps or len(cleaned_w) <= 1:
            continue
        if cleaned_w.lower() in _COMMON_RESUME_WORDS:
            continue
        result.add(cleaned_w)
    return result


def classify_suggestion(
    original_text: str,
    suggested_text: str,
    candidate_tools: List[str],
) -> Tuple[str, str]:
    """
    Classify an AI suggestion's evidence status.

    Args:
        original_text:   The original resume text this suggestion replaces.
        suggested_text:  The AI-generated replacement.
        candidate_tools: All skills/tools from the candidate's full resume.

    Returns:
        (evidence_status, evidence_note)
        evidence_status: "supported" | "needs_confirmation" | "unsupported"
        evidence_note:   Human-readable explanation for the user.
    """
    if not suggested_text or not suggested_text.strip():
        return "unsupported", "Suggestion is empty."

    orig_lower = original_text.lower()
    sugg_lower = suggested_text.lower()
    tools_lower = {t.lower().strip() for t in candidate_tools if t and t.strip()}

    notes: List[str] = []
    status = "supported"

    # ── 1. Check for new numeric metrics ─────────────────────────────────────
    orig_nums = _extract_numbers(original_text)
    sugg_nums = _extract_numbers(suggested_text)
    new_nums = sugg_nums - orig_nums
    if new_nums:
        for pattern in _METRIC_PATTERNS:
            if re.search(pattern, suggested_text, re.IGNORECASE):
                new_num_snippet = ", ".join(sorted(new_nums)[:3])
                notes.append(
                    f"New metric(s) introduced ({new_num_snippet}) — "
                    "please confirm these numbers are accurate for your experience."
                )
                status = "needs_confirmation"
                break

    # ── 2. Check for new business-impact language ─────────────────────────────
    for pattern in _IMPACT_PHRASES:
        m = re.search(pattern, suggested_text, re.IGNORECASE)
        if m and not re.search(pattern, original_text, re.IGNORECASE):
            notes.append(
                f"Business-impact claim ('{m.group()}') not in original — "
                "confirm this is accurate."
            )
            status = "needs_confirmation"
            break

    # ── 3. Check for new technology/tool names ────────────────────────────────
    orig_techs = _extract_tech_terms(original_text)
    sugg_techs = _extract_tech_terms(suggested_text)
    new_techs = sugg_techs - orig_techs

    def is_tool_known(tech: str) -> bool:
        t_clean = _clean_term(tech).lower()
        if not t_clean or len(t_clean) <= 1:
            return True
        if t_clean in tools_lower or t_clean in orig_lower:
            return True
        if tech.lower() in tools_lower or tech.lower() in orig_lower:
            return True
        # Substring / partial match against known tools
        for known in tools_lower:
            if t_clean in known or known in t_clean:
                return True
        return False

    truly_new = {t for t in new_techs if not is_tool_known(t)}
    if truly_new:
        tech_list = ", ".join(sorted(truly_new)[:4])
        notes.append(
            f"New tool/technology mentioned ('{tech_list}') not found in original — "
            "remove if you did not use it."
        )
        # Only escalate to unsupported if it's a substantive multi-char tech claim
        significant_new = {t for t in truly_new if len(t) > 2}
        if significant_new:
            status = "unsupported" if status == "supported" else status

    # ── 4. Check for credential / certification claims ─────────────────────────
    for pattern in _CREDENTIAL_PATTERNS:
        m = re.search(pattern, suggested_text, re.IGNORECASE)
        if m and not re.search(pattern, original_text, re.IGNORECASE):
            notes.append(
                f"New credential/certification claim ('{m.group()}') — "
                "only include if you hold this qualification."
            )
            status = "unsupported"
            break

    # ── 5. Check for unsupported action verbs added by the AI ─────────────────
    # Verbs that are strong factual claims (not merely stylistic improvements)
    _UNSUPPORTED_VERBS = {
        "deployed", "led", "managed", "directed", "oversaw", "spearheaded",
        "architected", "scaled", "migrated", "optimized",
    }
    orig_words = set(re.findall(r"\b\w+\b", orig_lower))
    sugg_words = set(re.findall(r"\b\w+\b", sugg_lower))
    new_verbs = _UNSUPPORTED_VERBS & (sugg_words - orig_words)
    if new_verbs:
        v_list = ", ".join(sorted(new_verbs)[:3])
        notes.append(
            f"AI added strong action verb(s) ({v_list}) not in your original — "
            "keep only if it accurately reflects your contribution."
        )
        if status == "supported":
            status = "needs_confirmation"

    # ── 5b. Check for placeholder metrics left in (model asked for confirmation) ─
    placeholders = re.findall(r"\[[A-Z%$\d\s]+\]", suggested_text)
    if placeholders:
        ph_list = ", ".join(placeholders[:3])
        notes.append(
            f"Metric placeholder(s) {ph_list} — fill in your actual numbers "
            "before accepting."
        )
        if status == "supported":
            status = "needs_confirmation"

    # ── Build evidence note ───────────────────────────────────────────────────
    if not notes:
        evidence_note = "Suggestion improves phrasing and action verbs without adding new factual claims."
    else:
        evidence_note = " | ".join(notes)

    return status, evidence_note


def guard_suggestions(
    suggestions: list,
    candidate_tools: List[str],
) -> list:
    """
    Apply hallucination guard to a list of suggestion dicts in-place.
    Each suggestion dict must have 'original_text' and 'suggested_text' keys.
    Adds/updates 'evidence_status' and 'evidence_note' fields.
    """
    for s in suggestions:
        orig = s.get("original_text", "")
        sugg = s.get("suggested_text", "")
        status, note = classify_suggestion(orig, sugg, candidate_tools)
        s["evidence_status"] = status
        s["evidence_note"] = note
    return suggestions
