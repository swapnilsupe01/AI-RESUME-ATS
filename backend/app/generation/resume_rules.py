"""
Resume-Style Rules Engine.

Implements core domain rules for high-impact technical resumes:
  1. Weak Verbs: Detects passive or vague verbs and upgrades to strong action verbs.
  2. Bullet Length: Flags bullets that are too short (under 8-10 words) or run-on (over 30-35 words).
  3. Missing Metrics: Detects whether bullet points lack quantifiable numbers, percentages, or scale.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Mapping of weak or passive verbs / phrases to strong action verb upgrades
WEAK_VERB_MAP: Dict[str, List[str]] = {
    "worked on": ["Engineered", "Developed", "Architected", "Spearheaded", "Implemented"],
    "work on": ["Engineer", "Develop", "Architect", "Spearhead", "Implement"],
    "helped with": ["Collaborated on", "Supported", "Facilitated", "Engineered"],
    "helped": ["Facilitated", "Accelerated", "Collaborated to deliver", "Bolstered"],
    "assisted with": ["Collaborated on", "Co-developed", "Contributed to"],
    "assisted": ["Collaborated on", "Co-developed", "Supported"],
    "responsible for": ["Led", "Directed", "Orchestrated", "Managed", "Executed"],
    "participated in": ["Collaborated on", "Contributed to", "Co-engineered"],
    "handled": ["Orchestrated", "Administered", "Executed", "Resolved"],
    "aided": ["Facilitated", "Bolstered", "Supported"],
    "involved in": ["Contributed to", "Partnered in", "Delivered"],
    "tried to": ["Strove to", "Initiated efforts to"],
    "tasked with": ["Spearheaded", "Appointed to lead", "Executed"],
    "served as": ["Led as", "Spearheaded as", "Functioned as"],
    "dealt with": ["Resolved", "Mitigated", "Managed"],
    "was part of": ["Collaborated with", "Contributed to"],
    "did": ["Executed", "Performed", "Implemented"],
    "made": ["Built", "Produced", "Engineered", "Developed"],
    "got": ["Acquired", "Achieved", "Secured"],
    "looked at": ["Analyzed", "Audited", "Evaluated", "Inspected"],
    "changed": ["Refactored", "Transformed", "Modernized", "Optimized"],
}

# Strong action verbs for recommendations
STRONG_ACTION_VERBS = [
    "Architected", "Spearheaded", "Engineered", "Orchestrated",
    "Implemented", "Optimized", "Automated", "Streamlined",
    "Executed", "Deployed", "Formulated", "Integrated",
    "Pioneered", "Scaled", "Designed", "Standardized"
]

# Patterns for quantifiable metrics
METRIC_PATTERNS = [
    re.compile(r'\b\d+(?:\.\d+)?%\b'),                                    # Percentages: 45%, 99.9%
    re.compile(r'\$\s*\d+[\d,]*(?:\.\d+)?\s*(?:k|m|b|million|billion)?\b', re.I),  # Currency: $50k, $1.2M
    re.compile(r'\b\d+(?:\.\d+)?\s*(?:x|X)\b'),                          # Multipliers: 3x, 10x
    re.compile(r'\b\d+[\d,]*\+'),                                         # Plus scales: 50+, 1,000+
    re.compile(r'\b\d+[\d,]*\s*(?:users|clients|rps|req/s|queries|nodes|clusters|endpoints|microservices|pipelines|records|rows|datasets|prs|commits)\b', re.I),
    re.compile(r'\b\d+\s*(?:ms|seconds?|mins?|minutes?|hours?|hrs?|days?|weeks?|months?)\b', re.I),  # Latency/time
    re.compile(r'\b\d+(?:\.\d+)?\s*(?:GB|TB|MB|PB|kbps|mbps|gbps)\b', re.I),  # Data/speed
    re.compile(r'\b\d{2,}\b'),                                            # Generic integers >= 10
]


def check_weak_verbs(text: str) -> List[Dict[str, Any]]:
    """
    Detect weak, passive, or vague verbs in the text.
    Returns a list of detected weak verbs with suggested strong alternatives.
    """
    if not text:
        return []

    issues = []
    text_lower = text.lower().strip()

    # Sort weak verbs by length descending to match multi-word phrases first
    sorted_weak = sorted(WEAK_VERB_MAP.keys(), key=lambda k: len(k), reverse=True)

    for weak in sorted_weak:
        # Match as word boundary or start of sentence
        pattern = rf'\b{re.escape(weak)}\b'
        match = re.search(pattern, text_lower)
        if match:
            suggestions = WEAK_VERB_MAP[weak]
            is_opener = match.start() < 10
            issues.append({
                "type": "weak_verb",
                "matched_text": weak,
                "is_opener": is_opener,
                "suggestions": suggestions,
                "message": f"Weak verb phrase '{weak}' detected{ ' as sentence opener' if is_opener else ''}. "
                           f"Consider stronger action verbs: {', '.join(suggestions[:3])}."
            })

    return issues


def upgrade_weak_verbs(text: str) -> str:
    """
    Automatically upgrade weak verb openers to strong executive action verbs.
    Example: 'Worked on developing REST APIs' -> 'Engineered REST APIs'
    """
    if not text:
        return text

    s = text.strip()
    s_lower = s.lower()

    # Check for weak openers
    for weak, replacements in sorted(WEAK_VERB_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = rf'^{re.escape(weak)}\b\s*'
        match = re.search(pattern, s_lower)
        if match:
            rep = replacements[0]
            # Replace at start preserving capitalization
            remainder = s[match.end():]
            # If followed by another gerund (e.g. "Worked on developing"), convert that directly
            gerund_match = re.match(r'^(developing|building|creating|designing|implementing|testing)\s+', remainder, re.I)
            if gerund_match:
                g_word = gerund_match.group(1).lower()
                past_form = {
                    "developing": "Developed", "building": "Built", "creating": "Created",
                    "designing": "Designed", "implementing": "Implemented", "testing": "Tested"
                }.get(g_word, rep)
                return past_form + " " + remainder[gerund_match.end():]

            return rep + " " + remainder

    return s


def check_bullet_length(text: str, min_words: int = 8, max_words: int = 32) -> Dict[str, Any]:
    """
    Evaluate the word length of a resume bullet point.
    Ideal length is 10-30 words.
    """
    if not text:
        return {
            "word_count": 0,
            "status": "empty",
            "message": "Bullet is empty."
        }

    words = re.findall(r'[a-zA-Z0-9_\-\.]+', text.strip())
    wc = len(words)

    if wc < min_words:
        return {
            "word_count": wc,
            "status": "too_short",
            "message": f"Bullet is too short ({wc} words; min recommended is {min_words}). "
                       f"Add context, action taken, and measurable impact."
        }
    elif wc > max_words:
        return {
            "word_count": wc,
            "status": "too_long",
            "message": f"Bullet is too long ({wc} words; max recommended is {max_words}). "
                       f"Condense or split into multiple concise bullet points."
        }
    else:
        return {
            "word_count": wc,
            "status": "optimal",
            "message": f"Optimal bullet length ({wc} words)."
        }


def check_metrics(text: str) -> Dict[str, Any]:
    """
    Check whether a bullet point contains quantifiable metrics / measurable outcomes.
    """
    if not text:
        return {"has_metrics": False, "metrics_found": [], "message": "No text provided."}

    detected = []
    for pat in METRIC_PATTERNS:
        matches = pat.findall(text)
        if matches:
            detected.extend(matches)

    # Deduplicate while preserving order
    unique_metrics = list(dict.fromkeys(detected))

    has_metrics = len(unique_metrics) > 0
    message = (
        f"Found {len(unique_metrics)} quantifiable metric(s): {', '.join(unique_metrics)}"
        if has_metrics
        else "Missing quantifiable metrics. Include measurable numbers, percentages (e.g. 35%), scale (e.g. 10k+ users), or latency improvements."
    )

    return {
        "has_metrics": has_metrics,
        "metrics_found": unique_metrics,
        "message": message,
    }


def analyze_resume_bullet(text: str) -> Dict[str, Any]:
    """
    Comprehensive evaluation of a resume bullet against domain style rules:
      - Weak verbs
      - Bullet length
      - Missing metrics
    Returns structured audit result, quality score (0-100), and issues list.
    """
    if not text or not text.strip():
        return {
            "score": 0,
            "issues": ["Empty bullet point."],
            "length": {"word_count": 0, "status": "empty"},
            "weak_verbs": [],
            "metrics": {"has_metrics": False, "metrics_found": []},
            "improved_text": "",
        }

    issues: List[str] = []
    score = 100

    # 1. Weak verb analysis
    weak_issues = check_weak_verbs(text)
    if weak_issues:
        score -= min(30, len(weak_issues) * 15)
        for w in weak_issues:
            issues.append(w["message"])

    # 2. Length check
    len_res = check_bullet_length(text)
    if len_res["status"] == "too_short":
        score -= 20
        issues.append(len_res["message"])
    elif len_res["status"] == "too_long":
        score -= 15
        issues.append(len_res["message"])

    # 3. Metrics check
    met_res = check_metrics(text)
    if not met_res["has_metrics"]:
        score -= 25
        issues.append(met_res["message"])

    # Attempt automatic rule-based improvement
    improved_text = upgrade_weak_verbs(text)

    return {
        "score": max(0, score),
        "issues": issues,
        "length": len_res,
        "weak_verbs": weak_issues,
        "metrics": met_res,
        "improved_text": improved_text,
    }
