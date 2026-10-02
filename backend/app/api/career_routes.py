"""
Career Intelligence API Routes — Layer F
Exposes all career intelligence endpoints including academic year detection,
claim analysis, evidence mapping, interview kit, roadmap, and unified pipeline.
"""

import json
import os
from pathlib import Path
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query

from app.career_intelligence.schemas import (
    # Phase 1
    SkillGapRequest,
    RoadmapRequest,
    Resource,
    ResourceQuery,
    InterviewStartRequest,
    InterviewAnswerRequest,
    AssessmentStartRequest,
    AssessmentSubmitRequest,
    # Phase 2
    AcademicYearRequest,
    ClaimAnalysisRequest,
    InterviewKitRequest,
    CareerFullAnalysisRequest,
    MilestoneCompleteRequest,
    SkillVerifyRequest,
    ResourceOpenedRequest,
    CareerContext,
    CertificationAdvisorRequest,
    ToolAdvisorRequest,
)
from app.career_intelligence.skill_gap_engine import analyze_gaps
from app.career_intelligence.roadmap_generator import generate_roadmap
from app.career_intelligence.resource_ranker import rank_resources
from app.career_intelligence.interview_engine import (
    start_interview,
    evaluate_answer,
)
from app.career_intelligence.assessment_engine import (
    create_assessment,
    score_assessment,
)
from app.career_intelligence.progress_tracker import (
    new_session,
    record_event,
    get_progress,
    complete_milestone,
    verify_skill,
    record_resource_opened,
    clear_session,
)
from app.career_intelligence.academic_year_detector import detect_academic_year
from app.career_intelligence.claim_analyzer import analyze_resume_claims
from app.career_intelligence.evidence_mapper import map_claim_evidence, summarize_evidence_profile
from app.career_intelligence.interview_kit import generate_interview_kit
from app.career_intelligence.prerequisite_graph import prerequisites_for
from app.career_intelligence.certification_advisor import (
    recommend_certifications,
    recommend_tools,
)
from app.career_intelligence.schemas import SkillEvidence

router = APIRouter(
    prefix="/api/career",
    tags=["Layer F — Career Intelligence"],
)

_INTERVIEWS: Dict[str, dict] = {}
_ASSESSMENTS: Dict[str, dict] = {}


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health")
def health():
    return {
        "status": "ok",
        "layer": "F",
        "phase": 2,
        "modules": [
            "academic_year_detector",
            "skill_gap_engine",
            "claim_analyzer",
            "evidence_mapper",
            "interview_kit",
            "roadmap_generator",
            "resource_ranker",
            "progress_tracker",
            "certification_advisor",
        ],
    }


# ── Phase 1 Endpoints ──────────────────────────────────────────────────────────

@router.post("/skill-gaps")
def skill_gaps(request: SkillGapRequest):
    """Analyze and rank skill gaps by priority with explainable evidence breakdown."""
    return {
        "target_role": request.context.target_role,
        "skill_gaps": analyze_gaps(request.skills, request.context),
    }


@router.post("/roadmap")
def roadmap(request: RoadmapRequest):
    """Generate a prerequisite-ordered, stage-aware learning roadmap."""
    return generate_roadmap(request.skill_gaps, request.context)


def _load_resources() -> List[Resource]:
    """Load learning resources from the configured JSON file."""
    configured_path = os.getenv("CAREER_RESOURCES_PATH")
    path = Path(configured_path) if configured_path else (
        Path(__file__).resolve().parents[1] / "learning_resources" / "resources.json"
    )

    if not path.is_file():
        return []

    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, list):
            raise ValueError("resources.json must contain a JSON list.")
        return [Resource(**item) for item in raw]
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load learning resources: {exc}",
        ) from exc


@router.get("/resources")
def resources(
    skill: str = Query(..., min_length=1),
    language: str = Query("Both", pattern="^(English|Hindi|Both)$"),
    level: str = Query("all", pattern="^(beginner|intermediate|advanced|all)$"),
    limit: int = Query(10, ge=1, le=50),
):
    """Retrieve ranked learning resources for a specific skill."""
    query = ResourceQuery(skill=skill, language=language, level=level, limit=limit)
    return {
        "skill": skill,
        "results": rank_resources(_load_resources(), query),
    }


@router.post("/interview/start")
def interview_start(request: InterviewStartRequest):
    """Start a new interview session with generated questions."""
    result = start_interview(
        request.target_role,
        request.job_description,
        request.projects,
        request.skill_gaps,
        request.difficulty,
        request.count,
    )
    _INTERVIEWS[result["session_id"]] = result
    return result


@router.post("/interview/answer")
def interview_answer(request: InterviewAnswerRequest):
    """Submit an answer for an interview question and get evaluated feedback."""
    session = _INTERVIEWS.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found or expired.")

    question = next(
        (q for q in session["questions"] if q["question_id"] == request.question_id),
        None,
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found in session.")

    result = evaluate_answer(request.answer, question["rubric"])
    record_event(
        request.session_id,
        "interview_answered",
        {"question_id": request.question_id, "score": result["score"]},
    )
    return {"question_id": request.question_id, "evaluation": result}


@router.post("/assessment/start")
def assessment_start(request: AssessmentStartRequest):
    """Start a new skill assessment session."""
    assessment = create_assessment(request.skill, request.level)
    assessment["session_id"] = new_session()
    _ASSESSMENTS[assessment["assessment_id"]] = assessment
    record_event(
        assessment["session_id"],
        "assessment_started",
        {"assessment_id": assessment["assessment_id"], "skill": request.skill},
    )
    return assessment


@router.post("/assessment/submit")
def assessment_submit(request: AssessmentSubmitRequest):
    """Submit assessment answers and receive scored results."""
    assessment = _ASSESSMENTS.get(request.assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found or expired.")
    if assessment["session_id"] != request.session_id:
        raise HTTPException(status_code=400, detail="Session does not match assessment.")

    result = score_assessment(assessment, request.answers, request.completed_task)
    record_event(request.session_id, "assessment_submitted", result)
    return result


@router.get("/progress/{session_id}")
def progress(session_id: str):
    """Retrieve aggregated learning progress for a session."""
    return get_progress(session_id)


# ── Phase 2 Endpoints ─────────────────────────────────────────────────────────

@router.post("/academic-year")
def academic_year(request: AcademicYearRequest):
    """
    Detect academic year and stage from education records and resume text.
    Returns structured stage classification with confidence, evidence, and conflict detection.
    """
    result = detect_academic_year(
        education_entries=request.education_entries,
        raw_text=request.raw_text,
        confirmed_stage=request.confirmed_stage,
    )
    return result.model_dump()


@router.post("/claim-analysis")
def claim_analysis(request: ClaimAnalysisRequest):
    """
    Extract and analyze all technical claims from resume projects, experience, and summary.
    Optionally maps claims against GitHub forensics evidence.
    """
    claims = analyze_resume_claims(
        projects=request.projects,
        experience=request.experience,
        summary=request.summary,
        extracted_skills=request.extracted_skills,
    )

    if request.github_forensics:
        claims = map_claim_evidence(
            claims,
            github_forensics=request.github_forensics,
        )

    profile = summarize_evidence_profile(claims)

    return {
        "total_claims": len(claims),
        "evidence_profile": profile,
        "claims": [c.model_dump() for c in claims],
    }


@router.post("/interview-kit")
def interview_kit(request: InterviewKitRequest):
    """
    Generate a stage-adapted, claim-linked recruiter interview kit.
    """
    kit = generate_interview_kit(
        target_role=request.target_role,
        academic_stage=request.academic_stage,  # type: ignore
        skill_gaps=request.skill_gaps,
        projects=request.projects,
        target_count=request.total_questions,
    )
    return kit


@router.post("/analyze-full")
def analyze_full(request: CareerFullAnalysisRequest):
    """
    Unified AI Career Intelligence pipeline.
    Runs: Academic Year Detection → Skill Gap Analysis → Claim Analysis
          → Evidence Mapping → Interview Kit → Learning Roadmap
    in one consolidated API call.
    """
    session_id = new_session()

    # ── 1. Academic Year Detection ────────────────────────────────────────────
    academic_result = detect_academic_year(
        education_entries=request.education_entries,
        raw_text=request.resume_text,
        confirmed_stage=request.confirmed_academic_stage,
    )
    academic_year_num = academic_result.academic_year
    academic_stage = academic_result.academic_stage

    record_event(session_id, "career_analyze_full_run", {
        "target_role": request.target_role,
        "academic_stage": academic_stage,
    })

    # ── 2. Skill Gap Analysis ─────────────────────────────────────────────────
    context = CareerContext(
        target_role=request.target_role,
        academic_year=academic_year_num,
        months_to_placement=request.months_to_placement,
        hours_per_week=request.hours_per_week,
        language=request.language_preference,  # type: ignore
    )

    jd_skills = request.jd_skills or []
    skill_gap_results = analyze_gaps(jd_skills, context) if jd_skills else []

    # ── 3. Learning Roadmap ───────────────────────────────────────────────────
    roadmap_result = {}
    if request.generate_roadmap and jd_skills:
        roadmap_result = generate_roadmap(jd_skills, context)
    record_event(session_id, "roadmap_generated", {"skills_count": len(jd_skills)})

    # ── 4. Claim Analysis ─────────────────────────────────────────────────────
    claims = analyze_resume_claims(
        projects=request.projects,
        experience=request.experience,
        summary=request.summary,
        extracted_skills=request.extracted_skills,
    )

    # ── 5. Evidence Mapping ───────────────────────────────────────────────────
    if request.github_forensics:
        claims = map_claim_evidence(claims, github_forensics=request.github_forensics)
    evidence_profile = summarize_evidence_profile(claims)

    # ── 6. Recruiter Interview Kit ────────────────────────────────────────────
    interview_kit_result = {}
    if request.generate_interview_kit:
        gap_skill_names = [s.skill for s in jd_skills] if jd_skills else []
        project_names = [p.get("name", "Project") for p in (request.projects or [])]
        interview_kit_result = generate_interview_kit(
            target_role=request.target_role,
            academic_stage=academic_stage,  # type: ignore
            claims=claims,
            skill_gaps=gap_skill_names,
            projects=project_names,
            target_count=request.total_interview_questions,
        )

    # ── 7. Certification & Tool Recommendations ────────────────────────────
    gap_skill_names_for_certs = [s.skill for s in jd_skills] if jd_skills else []
    cert_recommendations = recommend_certifications(
        academic_stage=academic_stage,  # type: ignore
        jd_skill_gaps=gap_skill_names_for_certs,
        existing_certifications=None,
        max_recommendations=5,
    )
    tool_recommendations = recommend_tools(
        jd_skill_gaps=gap_skill_names_for_certs,
        academic_stage=academic_stage,  # type: ignore
        max_per_skill=2,
    )

    return {
        "session_id": session_id,
        "target_role": request.target_role,
        "academic_year_detection": academic_result.model_dump(),
        "skill_gap_analysis": {
            "target_role": request.target_role,
            "skill_gaps": skill_gap_results,
        },
        "learning_roadmap": roadmap_result,
        "claim_analysis": {
            "total_claims": len(claims),
            "evidence_profile": evidence_profile,
            "claims": [c.model_dump() for c in claims],
        },
        "recruiter_interview_kit": interview_kit_result,
        "certification_recommendations": cert_recommendations,
        "tool_recommendations": tool_recommendations,
        "pipeline_note": (
            "All analysis is deterministic and explainable. "
            "No LLM or external API call was made. "
            "Certifications are stage-calibrated to the student's academic year and JD skill gaps. "
            "Evidence mapping uses public GitHub data only — insufficient evidence is never penalized."
        ),
    }


# ── Certification & Tool Advisor Endpoints ─────────────────────────────────────

@router.post("/certifications")
def certifications(request: CertificationAdvisorRequest):
    """
    Recommend stage-appropriate certifications based on academic year and JD skill gaps.

    Returns three lists:
    - recommended: Certifications you should pursue NOW (stage + JD aligned)
    - save_for_later: Too advanced for current stage — revisit after progressing
    - already_held: Certs already detected on your resume
    """
    return recommend_certifications(
        academic_stage=request.academic_stage,  # type: ignore
        jd_skill_gaps=request.jd_skill_gaps,
        existing_certifications=request.existing_certifications,
        max_recommendations=request.max_recommendations,
    )


@router.post("/tools")
def tools(request: ToolAdvisorRequest):
    """
    Recommend free developer tools for each JD skill gap, calibrated to academic stage.
    All recommended tools are free and open-source unless otherwise noted.
    """
    return recommend_tools(
        jd_skill_gaps=request.jd_skill_gaps,
        academic_stage=request.academic_stage,  # type: ignore
        max_per_skill=request.max_per_skill,
    )


# ── Progress Tracking Phase 2 Endpoints ───────────────────────────────────────

@router.post("/progress/milestone")
def milestone_complete(request: MilestoneCompleteRequest):
    """Mark a learning milestone as completed."""
    event = complete_milestone(request.session_id, request.skill, request.milestone_text)
    return {"message": "Milestone recorded.", "event": event}


@router.post("/progress/verify-skill")
def skill_verify(request: SkillVerifyRequest):
    """Mark a skill as independently verified with optional evidence URL."""
    event = verify_skill(
        request.session_id,
        request.skill,
        request.evidence_url,
        request.notes,
    )
    return {"message": "Skill verification recorded.", "event": event}


@router.post("/progress/resource-opened")
def resource_opened(request: ResourceOpenedRequest):
    """Log that a learning resource was accessed."""
    event = record_resource_opened(
        request.session_id,
        request.resource_id,
        request.skill,
        request.title,
    )
    return {"message": "Resource access recorded.", "event": event}


@router.delete("/progress/{session_id}")
def clear_progress(session_id: str):
    """Clear all progress events for a session."""
    clear_session(session_id)
    return {"message": f"Session '{session_id}' cleared."}