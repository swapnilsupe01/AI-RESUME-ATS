from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


# ── Existing Phase 1 Schemas ──────────────────────────────────────────────────

class SkillEvidence(BaseModel):
    skill: str
    jd_importance: float = Field(default=0.7, ge=0, le=1)
    resume_evidence: float = Field(default=0.0, ge=0, le=1)
    project_evidence: float = Field(default=0.0, ge=0, le=1)
    github_evidence: float = Field(default=0.0, ge=0, le=1)
    current_level: Literal["unknown", "beginner", "intermediate", "advanced"] = "unknown"
    prerequisite_gaps: List[str] = Field(default_factory=list)


class CareerContext(BaseModel):
    target_role: str = "Software Developer"
    academic_year: Optional[int] = Field(default=None, ge=1, le=6)
    months_to_internship: Optional[float] = Field(default=None, ge=0)
    months_to_placement: Optional[float] = Field(default=None, ge=0)
    hours_per_week: float = Field(default=5, gt=0, le=80)
    language: Literal["English", "Hindi", "Both"] = "Both"


class SkillGapRequest(BaseModel):
    skills: List[SkillEvidence]
    context: CareerContext = Field(default_factory=CareerContext)


class Resource(BaseModel):
    id: str
    skill: str
    title: str
    url: str
    language: Literal["English", "Hindi", "Both"] = "English"
    source_type: Literal["official_docs", "youtube", "course", "article", "practice"] = "article"
    difficulty: Literal["beginner", "intermediate", "advanced", "all"] = "all"
    topics: List[str] = Field(default_factory=list)
    hands_on: bool = False
    popularity_score: float = Field(default=0.0, ge=0, le=1)
    freshness_score: float = Field(default=0.7, ge=0, le=1)
    authority_score: float = Field(default=0.5, ge=0, le=1)
    last_verified: Optional[str] = None


class ResourceQuery(BaseModel):
    skill: str
    language: Literal["English", "Hindi", "Both"] = "Both"
    level: Literal["beginner", "intermediate", "advanced", "all"] = "all"
    limit: int = Field(default=10, ge=1, le=50)


class RoadmapRequest(BaseModel):
    skill_gaps: List[SkillEvidence]
    context: CareerContext = Field(default_factory=CareerContext)


class InterviewStartRequest(BaseModel):
    target_role: str
    job_description: str = ""
    projects: List[str] = Field(default_factory=list)
    skill_gaps: List[str] = Field(default_factory=list)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    count: int = Field(default=5, ge=1, le=20)


class InterviewAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    answer: str = Field(min_length=1, max_length=12000)


class AssessmentStartRequest(BaseModel):
    skill: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"


class AssessmentSubmitRequest(BaseModel):
    session_id: str
    assessment_id: str
    answers: Dict[str, str] = Field(default_factory=dict)
    completed_task: bool = False
    reflection: str = ""


# ── Phase 2 Schemas — Academic Year Detection ─────────────────────────────────

class AcademicYearRequest(BaseModel):
    """Request for academic year / stage detection."""
    education_entries: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Structured education records from canonical resume (degree, institution, start_date, end_date)."
    )
    raw_text: str = Field(
        default="",
        description="Raw resume text for explicit academic-year statement detection."
    )
    confirmed_stage: Optional[Literal[
        "first_year", "second_year", "third_year", "final_year", "graduated", "postgraduate"
    ]] = Field(
        default=None,
        description="Student manually confirmed academic stage (overrides auto-detection)."
    )


# ── Phase 2 Schemas — Claim Analysis ─────────────────────────────────────────

class ClaimAnalysisRequest(BaseModel):
    """Request for extracting technical claims from resume sections."""
    projects: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Structured project list (name, description, highlights, technologies)."
    )
    experience: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Structured work experience list (company, role, highlights, technologies)."
    )
    summary: str = Field(
        default="",
        description="Professional summary section text."
    )
    extracted_skills: Optional[List[str]] = Field(
        default=None,
        description="List of skills already extracted from the resume for cross-reference."
    )
    github_forensics: Optional[Dict[str, Any]] = Field(
        default=None,
        description="GitHub forensics data (repositories, languages, detected_skills)."
    )


# ── Phase 2 Schemas — Recruiter Interview Kit ─────────────────────────────────

class InterviewKitRequest(BaseModel):
    """Request for generating the full recruiter interview kit."""
    target_role: str = Field(default="Software Developer")
    academic_stage: Literal[
        "first_year", "second_year", "third_year", "final_year", "graduated", "postgraduate", "unknown"
    ] = "final_year"
    skill_gaps: Optional[List[str]] = Field(
        default=None,
        description="JD-required skills that need gap-filling."
    )
    projects: Optional[List[str]] = Field(
        default=None,
        description="List of project names to reference in questions."
    )
    total_questions: int = Field(default=8, ge=3, le=20)


# ── Phase 2 Schemas — Unified Full Analysis ──────────────────────────────────

class CareerFullAnalysisRequest(BaseModel):
    """
    Unified request for the full AI Career Intelligence pipeline.
    Accepts resume text/canonical data + JD + GitHub info.
    """
    resume_text: str = Field(default="", description="Raw resume text or Markdown.")
    job_description: str = Field(default="", description="Full job description text.")
    target_role: str = Field(default="Software Developer")
    education_entries: Optional[List[Dict[str, Any]]] = Field(default=None)
    projects: Optional[List[Dict[str, Any]]] = Field(default=None)
    experience: Optional[List[Dict[str, Any]]] = Field(default=None)
    extracted_skills: Optional[List[str]] = Field(default=None)
    summary: str = Field(default="")
    jd_skills: Optional[List[SkillEvidence]] = Field(
        default=None,
        description="Pre-computed skill gap analysis items. If not provided, basic extraction is attempted."
    )
    github_forensics: Optional[Dict[str, Any]] = Field(default=None)
    months_to_placement: Optional[float] = Field(default=None, ge=0)
    hours_per_week: float = Field(default=10.0, gt=0, le=80)
    language_preference: Literal["English", "Hindi", "Both"] = "Both"
    confirmed_academic_stage: Optional[str] = Field(default=None)
    generate_interview_kit: bool = Field(default=True)
    generate_roadmap: bool = Field(default=True)
    total_interview_questions: int = Field(default=8, ge=3, le=20)


# ── Phase 2 Schemas — Progress Tracking ─────────────────────────────────────

class MilestoneCompleteRequest(BaseModel):
    session_id: str
    skill: str
    milestone_text: str


class SkillVerifyRequest(BaseModel):
    session_id: str
    skill: str
    evidence_url: str = ""
    notes: str = ""


class ResourceOpenedRequest(BaseModel):
    session_id: str
    resource_id: str
    skill: str
    title: str


# ── Phase 2 Schemas — Certification & Tool Advisor ────────────────────────────

class CertificationAdvisorRequest(BaseModel):
    """Request to get stage-appropriate certification recommendations."""
    academic_stage: Literal[
        "first_year", "second_year", "third_year", "final_year",
        "graduated", "postgraduate", "unknown"
    ] = "second_year"
    jd_skill_gaps: List[str] = Field(
        default_factory=list,
        description="JD-required skills the student is missing or weak in."
    )
    existing_certifications: Optional[List[str]] = Field(
        default=None,
        description="Certifications already on the student's resume."
    )
    max_recommendations: int = Field(default=5, ge=1, le=10)


class ToolAdvisorRequest(BaseModel):
    """Request to get recommended developer tools per JD skill gap."""
    jd_skill_gaps: List[str] = Field(default_factory=list)
    academic_stage: Literal[
        "first_year", "second_year", "third_year", "final_year",
        "graduated", "postgraduate", "unknown"
    ] = "second_year"
    max_per_skill: int = Field(default=2, ge=1, le=5)
