"""
Enhanced Skill Gap Engine for Layer F — AI Career Intelligence Engine.
Produces structured, explainable gap analysis for every JD-required skill,
with evidence breakdown, prerequisite checks, and actionable next steps.
"""

from typing import Dict, List, Any
from .schemas import SkillEvidence, CareerContext

LEVEL_VALUE: Dict[str, float] = {
    "unknown": 0.0,
    "beginner": 0.25,
    "intermediate": 0.6,
    "advanced": 0.9,
}


def evidence_strength(item: SkillEvidence) -> float:
    """Weighted composite evidence score across resume, projects, and GitHub."""
    return (
        0.20 * item.resume_evidence
        + 0.35 * item.project_evidence
        + 0.45 * item.github_evidence
    )


def _urgency_factor(context: CareerContext) -> float:
    """Calculate urgency scalar from placement deadline and academic year."""
    urgency = 1.0
    if context.months_to_placement is not None:
        # Scale urgency from 0.35 (distant deadline) to 1.0 (imminent deadline)
        urgency = min(1.0, max(0.35, 1.0 / max(context.months_to_placement / 3.0, 1.0)))
    return urgency


def _knowledge_gap_estimate(item: SkillEvidence) -> float:
    """Gap from required mastery (1.0) to current level."""
    if item.current_level == "unknown":
        return 0.5  # Unknown = assume half gap by default
    return 1.0 - LEVEL_VALUE[item.current_level]


def _build_reason(
    item: SkillEvidence,
    evidence_gap: float,
    knowledge_gap: float,
    urgency: float,
) -> str:
    """Compose a human-readable explanation for priority ranking."""
    parts: List[str] = []

    # JD relevance
    if item.jd_importance >= 0.85:
        parts.append("critically required by the target job description")
    elif item.jd_importance >= 0.70:
        parts.append("highly relevant to the target role")
    else:
        parts.append("listed as preferred competency in the job description")

    # Knowledge status
    if item.current_level == "unknown":
        parts.append("mastery level is unknown and requires initial assessment")
    elif item.current_level == "beginner":
        parts.append("currently at beginner level with significant room to grow")

    # Evidence status
    if evidence_gap >= 0.80:
        parts.append("virtually no resume, project, or GitHub evidence found")
    elif evidence_gap >= 0.55:
        parts.append("limited verifiable evidence across resume and public repositories")

    # Urgency
    if urgency >= 0.90:
        parts.append("placement/internship deadline is imminent (< 3 months)")
    elif urgency >= 0.70:
        parts.append("moderate time pressure based on upcoming deadline")

    return "; ".join(parts) if parts else "relevant to the target job description"


def _build_evidence_breakdown(item: SkillEvidence) -> Dict[str, Any]:
    """Explainable breakdown of where evidence was found and what was missing."""
    breakdown = {
        "resume_evidence": item.resume_evidence,
        "project_evidence": item.project_evidence,
        "github_evidence": item.github_evidence,
        "overall_strength": round(evidence_strength(item), 3),
        "found": [],
        "missing": [],
    }

    if item.resume_evidence >= 0.5:
        breakdown["found"].append("Skill mentioned in resume text or skills section.")
    elif item.resume_evidence > 0.0:
        breakdown["found"].append("Partial mention in resume text (below threshold).")
    else:
        breakdown["missing"].append("No mention found in resume text or skills section.")

    if item.project_evidence >= 0.5:
        breakdown["found"].append("Applied in at least one project description or highlight.")
    elif item.project_evidence > 0.0:
        breakdown["found"].append("Tangentially referenced in project context.")
    else:
        breakdown["missing"].append("Not demonstrated in any listed project.")

    if item.github_evidence >= 0.5:
        breakdown["found"].append("Detected in public GitHub repositories (languages, topics, dependencies).")
    elif item.github_evidence > 0.0:
        breakdown["found"].append("Weak GitHub signal detected.")
    else:
        breakdown["missing"].append("Not found in any analyzed public GitHub repository.")

    return breakdown


def _next_action(item: SkillEvidence, target_role: str) -> str:
    """Recommend the single most impactful next action for this skill gap."""
    level = item.current_level
    if level == "unknown":
        return (
            f"Start with the official documentation for {item.skill} and complete "
            f"a beginner-level tutorial project to establish your baseline proficiency."
        )
    elif level == "beginner":
        return (
            f"Build a standalone {target_role}-relevant project incorporating {item.skill} "
            f"and push it to a public GitHub repository with a detailed README."
        )
    elif level == "intermediate":
        return (
            f"Extend your {item.skill} knowledge by integrating it into a live-deployed "
            f"project or contributing a meaningful fix to an open-source repository."
        )
    else:
        return (
            f"Deepen {item.skill} mastery through system design practice, "
            f"performance benchmarking, and security hardening exercises."
        )


def prioritize_skill(item: SkillEvidence, context: CareerContext) -> Dict[str, Any]:
    """
    Compute explainable priority score and evidence breakdown for one skill.
    """
    strength = evidence_strength(item)
    knowledge_gap = _knowledge_gap_estimate(item)
    evidence_gap = 1.0 - strength
    urgency = _urgency_factor(context)

    score = 100 * (
        0.40 * item.jd_importance
        + 0.25 * knowledge_gap
        + 0.20 * evidence_gap
        + 0.15 * urgency
    )

    return {
        "skill": item.skill,
        "priority_score": round(score, 1),
        "jd_importance": item.jd_importance,
        "current_level": item.current_level,
        "evidence_strength": round(strength, 3),
        "evidence_gap": round(evidence_gap, 3),
        "knowledge_gap_estimate": round(knowledge_gap, 3),
        "knowledge_uncertain": item.current_level == "unknown",
        "urgency_factor": round(urgency, 3),
        "prerequisite_gaps": item.prerequisite_gaps,
        "evidence_breakdown": _build_evidence_breakdown(item),
        "reason": _build_reason(item, evidence_gap, knowledge_gap, urgency),
        "why_it_matters": (
            f"'{item.skill}' is required/preferred in the target {context.target_role} role "
            f"(JD importance {int(item.jd_importance * 100)}%). "
            f"Closing this gap will directly strengthen your application evidence and "
            f"recruiter interview performance."
        ),
        "next_action": _next_action(item, context.target_role),
        "interpretation": (
            "Priority score is an explainable heuristic — "
            "not a trained ML prediction. Weights: JD importance (40%), "
            "knowledge gap (25%), evidence gap (20%), urgency (15%)."
        ),
    }


def analyze_gaps(skills: List[SkillEvidence], context: CareerContext) -> List[Dict]:
    """
    Analyze and rank all skills by gap priority.
    Returns a sorted list of explainable gap objects.
    """
    return sorted(
        [prioritize_skill(s, context) for s in skills],
        key=lambda x: x["priority_score"],
        reverse=True,
    )
