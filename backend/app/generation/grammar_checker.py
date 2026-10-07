"""
LanguageTool Grammar Layer — open-source local grammar checker via language_tool_python.

Configured as a dedicated grammar checking & correction layer instead of ad-hoc regex rules.
Unwanted rules, specifically Oxford comma rules and whitespace formatting rules, are disabled.
"""

import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cached LanguageTool singleton instance
_tool_instance = None
_tool_failed = False

# Rules to disable: specifically Oxford comma / serial comma rules and style rules
DISABLED_RULES = {
    "OXFORD_SPELLING_RULE",
    "OXFORD_COMMA",
    "COMMA_TAGGED_CONNECTIVE",
    "SERIAL_COMMA_ON_OFF",
    "EN_OXFORD_COMMA",
    "SERIAL_COMMA_PREFERENCE",
    "CONSECUTIVE_SPACES",
    "WHITESPACE_RULE",
}


def get_language_tool():
    """
    Lazy-load local LanguageTool instance with unwanted rules disabled.
    Handles missing package or JVM startup issues gracefully without crashing.
    """
    global _tool_instance, _tool_failed
    if _tool_failed:
        return None
    if _tool_instance is not None:
        return _tool_instance

    try:
        import language_tool_python

        # Initialize local language tool for en-US
        tool = language_tool_python.LanguageTool("en-US")

        # Disable unwanted rules (specifically Oxford comma checks)
        for rule_id in DISABLED_RULES:
            try:
                tool.disable_rule(rule_id)
            except Exception:
                pass

        _tool_instance = tool
        logger.info("[LanguageTool] Successfully initialized local grammar checker with Oxford comma disabled.")
        return _tool_instance
    except Exception as exc:
        logger.warning(
            "[LanguageTool] Could not initialize language_tool_python (%s: %s). "
            "Falling back to basic validation.",
            type(exc).__name__,
            exc,
        )
        _tool_failed = True
        return None


def is_grammar_tool_available() -> bool:
    """Return True if local LanguageTool is available and loaded."""
    tool = get_language_tool()
    return tool is not None


def check_grammar(text: str) -> List[Dict[str, Any]]:
    """
    Check text for grammatical issues using LanguageTool.
    Filters out any matches corresponding to disabled rules (like Oxford comma).

    Returns:
        List of issues with ruleId, message, context, offset, length, and suggested replacements.
    """
    if not text or not text.strip():
        return []

    tool = get_language_tool()
    if tool is None:
        return []

    try:
        matches = tool.check(text)
        results = []
        for match in matches:
            rule_id = getattr(match, "ruleId", "") or getattr(match, "rule_id", "")
            if rule_id in DISABLED_RULES or "OXFORD" in rule_id.upper() or "SERIAL_COMMA" in rule_id.upper():
                continue

            results.append({
                "rule_id": rule_id,
                "message": getattr(match, "message", ""),
                "context": getattr(match, "context", ""),
                "offset": getattr(match, "offset", 0),
                "error_length": getattr(match, "errorLength", getattr(match, "error_length", 0)),
                "replacements": getattr(match, "replacements", [])[:5],
                "category": getattr(match, "category", ""),
            })
        return results
    except Exception as exc:
        logger.warning("[LanguageTool] Check failed: %s", exc)
        return []


def correct_grammar(text: str) -> str:
    """
    Automatically correct grammar in the given text using LanguageTool,
    respecting disabled rules (Oxford comma is never forced or removed).
    If tool is unavailable, returns text unchanged.
    """
    if not text or not text.strip():
        return text

    tool = get_language_tool()
    if tool is None:
        return text

    try:
        matches = tool.check(text)
        # Filter out disabled rules
        valid_matches = [
            m for m in matches
            if (getattr(m, "ruleId", "") or getattr(m, "rule_id", "")) not in DISABLED_RULES
            and "OXFORD" not in (getattr(m, "ruleId", "") or getattr(m, "rule_id", "")).upper()
            and "SERIAL_COMMA" not in (getattr(m, "ruleId", "") or getattr(m, "rule_id", "")).upper()
        ]

        if not valid_matches:
            return text

        # Apply corrections from valid matches only
        import language_tool_python
        corrected = language_tool_python.utils.correct(text, valid_matches)
        return corrected
    except Exception as exc:
        logger.warning("[LanguageTool] Correction failed: %s", exc)
        return text
