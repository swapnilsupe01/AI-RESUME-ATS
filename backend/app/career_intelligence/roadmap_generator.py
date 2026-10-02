"""
Personalized Career Roadmap Generator for Layer F — AI Career Intelligence Engine.
Generates stage-aware, prerequisite-ordered learning roadmaps with milestones,
effort estimates, and recruiter-interview-aligned completion criteria.
"""

from typing import Dict, Any, List, Optional
from .schemas import SkillEvidence, CareerContext
from .skill_gap_engine import analyze_gaps
from .prerequisite_graph import prerequisites_for, topological_sort_skills

# Minutes of focused learning roughly needed per skill level, per week of available hours
_EFFORT_ESTIMATE: Dict[str, Dict[str, float]] = {
    "beginner":     {"weeks_min": 1, "weeks_max": 2},
    "intermediate": {"weeks_min": 2, "weeks_max": 4},
    "advanced":     {"weeks_min": 3, "weeks_max": 6},
    "unknown":      {"weeks_min": 2, "weeks_max": 3},
}

_STAGE_CONTEXT: Dict[str, Dict[str, Any]] = {
    "first_year": {
        "focus": "Computing fundamentals, programming basics, and small exploratory projects.",
        "milestone_suffix": "Build a standalone script or mini-project demonstrating the concept.",
        "max_parallel": 1,
    },
    "second_year": {
        "focus": "Programming depth, data structures & algorithms, and first hands-on projects.",
        "milestone_suffix": "Apply the skill in a structured mini-project with tests.",
        "max_parallel": 1,
    },
    "third_year": {
        "focus": "Role-specific development, project design, internship preparation, and debugging.",
        "milestone_suffix": "Integrate into your capstone or internship portfolio project.",
        "max_parallel": 2,
    },
    "final_year": {
        "focus": "End-to-end project ownership, deployment, security, and placement readiness.",
        "milestone_suffix": "Deploy a production-quality feature and document architecture decisions.",
        "max_parallel": 2,
    },
    "graduated": {
        "focus": "Advanced system design, open-source contributions, and job-specific depth.",
        "milestone_suffix": "Contribute an open-source fix or build a deployed side-project.",
        "max_parallel": 3,
    },
    "postgraduate": {
        "focus": "Research, specialization depth, and advanced engineering practices.",
        "milestone_suffix": "Produce a demonstrable outcome — paper summary, implementation, or experiment.",
        "max_parallel": 2,
    },
    "unknown": {
        "focus": "Core programming, computer science fundamentals, and beginner projects.",
        "milestone_suffix": "Build a small working prototype and document your learning.",
        "max_parallel": 1,
    },
}


def _build_roadmap_item(
    order: int,
    skill: str,
    priority_score: float,
    current_level: str,
    target_role: str,
    academic_stage: str,
    hours_per_week: float,
    prerequisite_gaps: List[str],
    months_to_deadline: Optional[float],
) -> Dict[str, Any]:
    """Construct a single roadmap milestone item for a skill."""
    stage_ctx = _STAGE_CONTEXT.get(academic_stage, _STAGE_CONTEXT["unknown"])
    effort = _EFFORT_ESTIMATE.get(current_level, _EFFORT_ESTIMATE["unknown"])

    # Scale weeks inversely with available hours (baseline = 5 hrs/week)
    base_hours = 5.0
    effort_scale = base_hours / max(hours_per_week, 1.0)
    est_weeks = round(min(effort["weeks_max"], max(effort["weeks_min"], effort["weeks_min"] * effort_scale)), 1)

    # Hard deadline clamp: if very close to placement, compress effort
    if months_to_deadline is not None and months_to_deadline < 2:
        est_weeks = min(est_weeks, 1.5)

    milestones = [
        f"Study core concepts and mental model of {skill} using official documentation.",
        f"Complete a guided tutorial or lab exercise focused specifically on {skill}.",
        f"Apply {skill} in a minimal working example scoped to {target_role} context.",
        f"Explain your {skill} implementation and its trade-offs to a peer or mentor.",
        stage_ctx["milestone_suffix"],
    ]

    completion_criteria = [
        f"Can articulate what {skill} is, what problem it solves, and when NOT to use it.",
        f"Has at least one code artefact using {skill} committed to a public repository.",
        f"Can answer a recruiter's intermediate-level interview question on {skill}.",
    ]

    return {
        "order": order,
        "skill": skill,
        "priority_score": priority_score,
        "current_level": current_level,
        "estimated_weeks": est_weeks,
        "weekly_hours": hours_per_week,
        "prerequisites_to_check": prerequisite_gaps or prerequisites_for(skill),
        "milestones": milestones,
        "practical_exercise": (
            f"Build a small {target_role.lower()} component using {skill} — "
            f"e.g. an API endpoint, data pipeline step, UI widget, or CLI script — "
            f"with at least one unit test. Push to GitHub."
        ),
        "completion_criteria": completion_criteria,
        "effort_note": (
            f"Estimate assumes {hours_per_week:.0f} hrs/week. "
            "Adjust based on your prior exposure. "
            "Effort is a starting point, not a guarantee."
        ),
    }


def generate_roadmap(
    skills: List[SkillEvidence],
    context: CareerContext,
) -> Dict[str, Any]:
    """
    Generate a personalized, prerequisite-ordered career roadmap.

    Parameters:
    - skills: List of SkillEvidence items (from skill-gap analysis).
    - context: CareerContext with role, academic year, hours, deadlines, language preference.

    Returns:
    - Structured roadmap with ordered phases, milestones, effort estimates, and stage context.
    """
    ranked = analyze_gaps(skills, context)

    # Topological sort to respect prerequisite ordering
    all_skill_names = [r["skill"] for r in ranked]
    ordered_names = topological_sort_skills(all_skill_names)

    # Re-index ranked gaps by their topo-sorted position
    ranked_index = {r["skill"].lower(): r for r in ranked}
    ordered_ranked = []
    for name in ordered_names:
        item = ranked_index.get(name.lower())
        if item:
            ordered_ranked.append(item)
    # Append any that weren't in topo result
    for r in ranked:
        if r not in ordered_ranked:
            ordered_ranked.append(r)

    # Recover original SkillEvidence objects for additional fields
    skills_index = {s.skill.lower(): s for s in skills}

    academic_stage = "unknown"
    if context.academic_year is not None:
        _stage_map = {1: "first_year", 2: "second_year", 3: "third_year", 4: "final_year"}
        academic_stage = _stage_map.get(context.academic_year, "final_year")

    stage_info = _STAGE_CONTEXT.get(academic_stage, _STAGE_CONTEXT["unknown"])

    roadmap_items = []
    for i, row in enumerate(ordered_ranked):
        skill_obj = skills_index.get(row["skill"].lower())
        current_level = skill_obj.current_level if skill_obj else "unknown"
        prereq_gaps = skill_obj.prerequisite_gaps if skill_obj else []

        roadmap_items.append(
            _build_roadmap_item(
                order=i + 1,
                skill=row["skill"],
                priority_score=row["priority_score"],
                current_level=current_level,
                target_role=context.target_role,
                academic_stage=academic_stage,
                hours_per_week=context.hours_per_week,
                prerequisite_gaps=prereq_gaps or prerequisites_for(row["skill"]),
                months_to_deadline=context.months_to_placement,
            )
        )

    # Phase grouping (simple): split into Phase 1 / Phase 2 / Phase 3
    total = len(roadmap_items)
    phase_size = max(1, total // 3)

    phases = {
        "phase_1_foundation": roadmap_items[:phase_size],
        "phase_2_depth": roadmap_items[phase_size: phase_size * 2],
        "phase_3_polish": roadmap_items[phase_size * 2:],
    }

    weeks_total = sum(item["estimated_weeks"] for item in roadmap_items)

    return {
        "target_role": context.target_role,
        "academic_stage": academic_stage,
        "stage_focus": stage_info["focus"],
        "language_preference": context.language,
        "available_hours_per_week": context.hours_per_week,
        "months_to_placement": context.months_to_placement,
        "total_estimated_weeks": round(weeks_total, 1),
        "ranked_gaps": ranked,
        "roadmap": roadmap_items,
        "phases": phases,
        "note": (
            "Time estimates are starting points; adapt after honest self-assessment. "
            "Prerequisite-ordered to ensure foundational concepts are covered before advanced topics. "
            "Academic stage is used to personalize milestones — not to restrict your opportunities."
        ),
    }
