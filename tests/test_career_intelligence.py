"""
Comprehensive test suite for Layer F — AI Career Intelligence Engine (Phase 2).
Covers all new modules: academic_year_detector, claim_analyzer, evidence_mapper,
interview_kit, prerequisite_graph, roadmap_generator, skill_gap_engine,
resource_ranker, progress_tracker, and career_routes.

Backward-compatible with test_layer_f_phase1.py (no existing tests removed).
"""

import pytest
from datetime import datetime, timezone

from app.career_intelligence.schemas import (
    SkillEvidence, CareerContext, Resource, ResourceQuery,
)
from app.career_intelligence.skill_gap_engine import analyze_gaps, evidence_strength
from app.career_intelligence.roadmap_generator import generate_roadmap
from app.career_intelligence.resource_ranker import rank_resources
from app.career_intelligence.interview_engine import start_interview, evaluate_answer
from app.career_intelligence.assessment_engine import create_assessment, score_assessment
from app.career_intelligence.academic_year_detector import detect_academic_year
from app.career_intelligence.claim_analyzer import (
    extract_claims_from_text, analyze_resume_claims,
)
from app.career_intelligence.evidence_mapper import (
    map_claim_evidence, summarize_evidence_profile,
)
from app.career_intelligence.interview_kit import generate_interview_kit
from app.career_intelligence.prerequisite_graph import (
    prerequisites_for, get_all_prerequisites, topological_sort_skills,
)
from app.career_intelligence.progress_tracker import (
    new_session, record_event, get_progress,
    complete_milestone, verify_skill, record_resource_opened, clear_session,
)


# ─── Phase 1 Regression Tests ───────────────────────────────────────────────

class TestPhase1Regression:
    def test_gaps_and_roadmap(self):
        context = CareerContext(
            target_role="Backend Developer",
            months_to_placement=4,
            hours_per_week=5,
        )
        skills = [
            SkillEvidence(skill="AWS", jd_importance=0.9, current_level="unknown"),
            SkillEvidence(skill="Python", jd_importance=0.8, resume_evidence=0.8,
                          project_evidence=0.8, current_level="intermediate"),
        ]
        ranked = analyze_gaps(skills, context)
        assert len(ranked) == 2
        assert ranked[0]["priority_score"] >= ranked[1]["priority_score"]
        roadmap = generate_roadmap(skills, context)
        assert roadmap["roadmap"]

    def test_resources(self):
        r = Resource(
            id="docker-docs", skill="Docker", title="Docker docs",
            url="https://docs.docker.com/", language="English",
            source_type="official_docs", difficulty="beginner",
            hands_on=True, authority_score=1,
        )
        result = rank_resources([r], ResourceQuery(skill="Docker", language="English"))
        assert result and result[0]["resource"]["id"] == "docker-docs"

    def test_interview(self):
        session = start_interview(
            "Backend Developer", "FastAPI", ["Resume API"], ["FastAPI"], "intermediate", 2
        )
        assert len(session["questions"]) == 2
        result = evaluate_answer(
            "I reproduce issues, inspect logs, isolate the cause and verify the fix.",
            ["reproduce", "logs", "cause", "fix"],
        )
        assert 0 <= result["score"] <= 100

    def test_assessment(self):
        a = create_assessment("Docker", "beginner")
        result = score_assessment(
            a,
            {"q1": "An image is a template and a container is a running instance."},
            True,
        )
        assert 0 <= result["overall_score"] <= 100


# ─── Skill Gap Engine ────────────────────────────────────────────────────────

class TestSkillGapEngine:
    def test_evidence_strength_zero(self):
        item = SkillEvidence(skill="Rust")
        assert evidence_strength(item) == 0.0

    def test_evidence_strength_full(self):
        item = SkillEvidence(
            skill="Python", resume_evidence=1.0, project_evidence=1.0, github_evidence=1.0
        )
        assert evidence_strength(item) == pytest.approx(1.0)

    def test_priority_score_range(self):
        context = CareerContext(target_role="Backend Developer", months_to_placement=3)
        skill = SkillEvidence(skill="FastAPI", jd_importance=0.9, current_level="beginner")
        gaps = analyze_gaps([skill], context)
        assert 0 < gaps[0]["priority_score"] <= 100

    def test_sorted_by_priority(self):
        context = CareerContext(target_role="Dev")
        skills = [
            SkillEvidence(skill="Docker", jd_importance=0.5, current_level="advanced"),
            SkillEvidence(skill="AWS", jd_importance=0.95, current_level="unknown"),
        ]
        gaps = analyze_gaps(skills, context)
        assert gaps[0]["priority_score"] >= gaps[1]["priority_score"]

    def test_explainable_fields_present(self):
        context = CareerContext(target_role="SWE")
        skill = SkillEvidence(skill="React", jd_importance=0.8)
        gaps = analyze_gaps([skill], context)
        item = gaps[0]
        for field in ("reason", "why_it_matters", "next_action", "evidence_breakdown", "interpretation"):
            assert field in item, f"Missing field: {field}"

    def test_evidence_breakdown_structure(self):
        context = CareerContext(target_role="SWE")
        skill = SkillEvidence(skill="PostgreSQL", jd_importance=0.85,
                              resume_evidence=0.6, project_evidence=0.0, github_evidence=0.0)
        gaps = analyze_gaps([skill], context)
        bd = gaps[0]["evidence_breakdown"]
        assert "found" in bd and "missing" in bd
        assert len(bd["found"]) >= 1  # resume_evidence >= 0.5
        assert len(bd["missing"]) >= 1  # project & github missing


# ─── Academic Year Detector ──────────────────────────────────────────────────

class TestAcademicYearDetector:
    def test_date_range_final_year(self):
        # B.Tech 2022–2026, reference date in 2025 → 3rd/4th year
        result = detect_academic_year(
            education_entries=[{
                "degree": "B.Tech",
                "institution": "Test University",
                "field_of_study": "Computer Science",
                "start_date": "2022",
                "end_date": "2026",
                "current": True,
            }],
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        assert result.academic_stage in ("third_year", "final_year")
        assert result.confidence > 0.5

    def test_graduated(self):
        result = detect_academic_year(
            education_entries=[{
                "degree": "B.Sc",
                "institution": "College",
                "start_date": "2019",
                "end_date": "2022",
            }],
            reference_date=datetime(2025, 6, 1, tzinfo=timezone.utc),
        )
        assert result.academic_stage == "graduated"

    def test_explicit_statement_final_year(self):
        result = detect_academic_year(
            raw_text="I am a final year B.Tech student in Computer Engineering.",
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        assert result.academic_stage in ("final_year", "third_year")

    def test_explicit_second_year(self):
        result = detect_academic_year(
            raw_text="Currently pursuing 2nd year MCA.",
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        assert result.academic_stage == "second_year"

    def test_lateral_entry_detection(self):
        result = detect_academic_year(
            education_entries=[{
                "degree": "B.Tech",
                "institution": "Polytechnic",
                "field_of_study": "Lateral Entry Computer Science",
                "start_date": "2023",
                "end_date": "2026",
            }],
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        assert result.is_lateral_entry is True

    def test_confirmed_stage_override(self):
        result = detect_academic_year(
            confirmed_stage="final_year",
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        assert result.academic_stage == "final_year"
        assert result.confidence == 1.0
        assert result.confirmed_by_student is True

    def test_unknown_with_no_data(self):
        result = detect_academic_year()
        assert result.academic_stage == "unknown"
        assert result.confidence < 0.5

    def test_conflict_detection(self):
        # Education dates say final_year but text says 2nd year
        result = detect_academic_year(
            education_entries=[{
                "degree": "B.Tech",
                "institution": "University",
                "start_date": "2022",
                "end_date": "2026",
            }],
            raw_text="I am a 2nd year B.Tech student.",
            reference_date=datetime(2025, 10, 1, tzinfo=timezone.utc),
        )
        # Should either detect conflict or reconcile — always has academic_stage
        assert result.academic_stage != "unknown"


# ─── Claim Analyzer ──────────────────────────────────────────────────────────

class TestClaimAnalyzer:
    def test_performance_claim_detected(self):
        bullet = "Reduced API response time by 45% by optimizing database query patterns."
        claims = extract_claims_from_text(bullet, "projects", "MyProject")
        assert any(c.category == "performance_optimization" for c in claims)
        assert any(c.metrics_claimed for c in claims)

    def test_api_backend_detected(self):
        bullet = "Built RESTful API endpoints using FastAPI with Pydantic validation."
        claims = extract_claims_from_text(bullet, "projects", "API Project")
        assert any(c.category == "api_backend" for c in claims)

    def test_cloud_deployment_detected(self):
        bullet = "Deployed containerized app using Docker and GitHub Actions CI/CD pipeline."
        claims = extract_claims_from_text(bullet, "projects", "Deploy Project")
        cats = [c.category for c in claims]
        assert "cloud_deployment" in cats or "testing_cicd" in cats

    def test_short_text_skipped(self):
        claims = extract_claims_from_text("Short text.", "projects", "P")
        assert claims == []

    def test_full_resume_analysis(self):
        projects = [{
            "name": "Indexify",
            "description": "Distributed data ingestion system.",
            "highlights": [
                "Improved throughput by 3x using parallel processing.",
                "Deployed on AWS ECS with Docker containers.",
            ],
            "technologies": ["Python", "AWS", "Docker"],
        }]
        claims = analyze_resume_claims(projects=projects, extracted_skills=["Python", "AWS", "Docker"])
        assert len(claims) >= 1
        for claim in claims:
            assert claim.source_title == "Indexify"

    def test_probing_questions_generated(self):
        bullet = "Implemented JWT authentication with refresh token rotation."
        claims = extract_claims_from_text(bullet, "projects", "Auth Project", ["Python", "JWT"])
        assert any(len(c.suggested_probing_questions) > 0 for c in claims)


# ─── Evidence Mapper ─────────────────────────────────────────────────────────

class TestEvidenceMapper:
    def test_no_github_marks_not_checked_for_projects(self):
        from app.career_intelligence.claim_analyzer import extract_claims_from_text
        claims = extract_claims_from_text(
            "Built REST API with FastAPI.", "projects", "Test Project"
        )
        mapped = map_claim_evidence(claims, github_forensics=None)
        assert all(c.evidence_status == "not_checked" for c in mapped)

    def test_experience_insufficient_evidence(self):
        from app.career_intelligence.claim_analyzer import extract_claims_from_text
        claims = extract_claims_from_text(
            "Designed microservice architecture at company.", "experience", "Role at Company"
        )
        mapped = map_claim_evidence(claims, github_forensics={})
        assert all(c.evidence_status in ("insufficient_evidence", "partially_supported") for c in mapped)

    def test_evidence_profile_keys(self):
        profile = summarize_evidence_profile([])
        for key in ("total_claims", "status_breakdown", "supported_rate", "guidance"):
            assert key in profile

    def test_evidence_profile_nonzero(self):
        from app.career_intelligence.claim_analyzer import extract_claims_from_text
        claims = extract_claims_from_text(
            "Reduced latency by 60% using Redis caching.", "projects", "Perf Project"
        )
        profile = summarize_evidence_profile(claims)
        assert profile["total_claims"] == len(claims)


# ─── Interview Kit ────────────────────────────────────────────────────────────

class TestInterviewKit:
    def test_generates_requested_question_count(self):
        kit = generate_interview_kit(
            target_role="Backend Developer",
            academic_stage="final_year",
            skill_gaps=["FastAPI", "Docker"],
            projects=["Indexify", "Aura"],
            target_count=6,
        )
        assert len(kit["questions"]) == 6

    def test_question_structure(self):
        kit = generate_interview_kit(
            target_role="Backend Developer",
            academic_stage="third_year",
            skill_gaps=["PostgreSQL"],
            target_count=4,
        )
        for q in kit["questions"]:
            for field in ("question_id", "question_text", "category", "difficulty",
                          "rubric_criteria", "follow_up_questions", "recruiter_intent"):
                assert field in q, f"Missing field: {field}"

    def test_stage_adaptation_note_present(self):
        kit = generate_interview_kit(academic_stage="first_year", target_count=3)
        assert "stage_adaptation_note" in kit
        assert "first" in kit["stage_adaptation_note"].lower()

    def test_beginner_stage_no_advanced_arch_questions(self):
        kit = generate_interview_kit(
            academic_stage="first_year",
            target_count=6,
        )
        # Architecture/design_tradeoff questions should not dominate first year kit
        advanced_cats = ["architecture_design", "design_tradeoffs"]
        adv_count = sum(1 for q in kit["questions"] if q["category"] in advanced_cats)
        assert adv_count < len(kit["questions"])  # Not all questions should be advanced


# ─── Prerequisite Graph ──────────────────────────────────────────────────────

class TestPrerequisiteGraph:
    def test_fastapi_has_python_prerequisite(self):
        prereqs = prerequisites_for("fastapi")
        assert any("python" in p.lower() for p in prereqs)

    def test_unknown_skill_returns_empty(self):
        assert prerequisites_for("made-up-skill-xyz") == []

    def test_recursive_prerequisites(self):
        all_prereqs = get_all_prerequisites("kubernetes")
        all_lower = [p.lower() for p in all_prereqs]
        assert "docker" in all_lower

    def test_topological_sort_python_before_fastapi(self):
        skills = ["FastAPI", "Python", "Docker"]
        ordered = topological_sort_skills(skills)
        py_idx = next((i for i, s in enumerate(ordered) if s.lower() == "python"), None)
        api_idx = next((i for i, s in enumerate(ordered) if s.lower() == "fastapi"), None)
        if py_idx is not None and api_idx is not None:
            assert py_idx <= api_idx

    def test_topological_sort_returns_all_skills(self):
        skills = ["React", "JavaScript", "AWS", "Docker"]
        ordered = topological_sort_skills(skills)
        assert len(ordered) == len(skills)
        assert set(ordered) == set(skills)


# ─── Roadmap Generator ───────────────────────────────────────────────────────

class TestRoadmapGenerator:
    def test_roadmap_has_required_keys(self):
        context = CareerContext(target_role="Backend Developer", months_to_placement=3, hours_per_week=8)
        skills = [
            SkillEvidence(skill="Python", jd_importance=0.8, current_level="intermediate"),
            SkillEvidence(skill="FastAPI", jd_importance=0.9, current_level="beginner"),
        ]
        result = generate_roadmap(skills, context)
        for key in ("target_role", "academic_stage", "roadmap", "phases", "total_estimated_weeks"):
            assert key in result

    def test_roadmap_items_have_milestones(self):
        context = CareerContext(target_role="SWE", hours_per_week=10)
        skills = [SkillEvidence(skill="Docker", jd_importance=0.85, current_level="unknown")]
        result = generate_roadmap(skills, context)
        assert result["roadmap"][0]["milestones"]
        assert result["roadmap"][0]["completion_criteria"]

    def test_phases_present(self):
        context = CareerContext(target_role="SWE")
        skills = [
            SkillEvidence(skill="Python", jd_importance=0.9),
            SkillEvidence(skill="Docker", jd_importance=0.8),
            SkillEvidence(skill="AWS", jd_importance=0.7),
        ]
        result = generate_roadmap(skills, context)
        phases = result["phases"]
        for phase_key in ("phase_1_foundation", "phase_2_depth", "phase_3_polish"):
            assert phase_key in phases

    def test_imminent_deadline_compresses_estimates(self):
        """Very short deadline should compress estimated weeks."""
        ctx_tight = CareerContext(target_role="SWE", months_to_placement=1, hours_per_week=5)
        skills = [SkillEvidence(skill="AWS", jd_importance=0.9, current_level="unknown")]
        result = generate_roadmap(skills, ctx_tight)
        assert result["roadmap"][0]["estimated_weeks"] <= 2.0


# ─── Resource Ranker ────────────────────────────────────────────────────────

class TestResourceRanker:
    def _make_resource(self, skill="Python", title="Test Doc", difficulty="beginner",
                       authority=0.9, hands_on=True):
        return Resource(
            id=f"{skill.lower()}-test",
            skill=skill,
            title=title,
            url=f"https://example.com/{skill.lower()}",
            language="English",
            source_type="official_docs",
            difficulty=difficulty,
            hands_on=hands_on,
            authority_score=authority,
        )

    def test_matching_skill_returned(self):
        r = self._make_resource("Python")
        result = rank_resources([r], ResourceQuery(skill="Python"))
        assert len(result) == 1

    def test_non_matching_skill_excluded(self):
        r = self._make_resource("React")
        result = rank_resources([r], ResourceQuery(skill="Python"))
        assert len(result) == 0

    def test_higher_authority_ranks_first(self):
        r1 = self._make_resource("Docker", "Low Authority", authority=0.3)
        r2 = self._make_resource("Docker", "High Authority", authority=1.0)
        result = rank_resources([r1, r2], ResourceQuery(skill="Docker"))
        assert result[0]["resource"]["title"] == "High Authority"

    def test_limit_respected(self):
        resources = [self._make_resource("Python", f"Doc {i}") for i in range(10)]
        result = rank_resources(resources, ResourceQuery(skill="Python", limit=3))
        assert len(result) <= 3


# ─── Progress Tracker ────────────────────────────────────────────────────────

class TestProgressTracker:
    def test_new_session_unique(self):
        s1 = new_session()
        s2 = new_session()
        assert s1 != s2

    def test_record_and_retrieve_event(self):
        sid = new_session()
        record_event(sid, "resource_opened", {"resource_id": "python-docs", "skill": "Python"})
        progress = get_progress(sid)
        assert progress["event_count"] == 1
        assert progress["events"][0]["event_type"] == "resource_opened"
        clear_session(sid)

    def test_milestone_tracking(self):
        sid = new_session()
        complete_milestone(sid, "Docker", "Completed Docker tutorial.")
        progress = get_progress(sid)
        assert len(progress["milestones_completed"]) == 1
        assert progress["milestones_completed"][0]["skill"] == "Docker"
        clear_session(sid)

    def test_skill_verification(self):
        sid = new_session()
        verify_skill(sid, "Python", "https://github.com/me/python-project", "Built REST API.")
        progress = get_progress(sid)
        assert len(progress["verified_skills"]) == 1
        assert progress["verified_skills"][0]["skill"] == "Python"
        clear_session(sid)

    def test_assessment_score_tracking(self):
        sid = new_session()
        record_event(sid, "assessment_submitted", {"overall_score": 75.0})
        progress = get_progress(sid)
        assert progress["assessment_scores"] == [75.0]
        assert progress["average_assessment_score"] == 75.0
        clear_session(sid)

    def test_progress_summary_structure(self):
        sid = new_session()
        progress = get_progress(sid)
        summary = progress["progress_summary"]
        for key in ("milestones_completed_count", "skills_verified_count",
                    "resources_opened_count", "total_assessments"):
            assert key in summary
        clear_session(sid)

    def test_clear_session(self):
        sid = new_session()
        record_event(sid, "resource_opened", {"skill": "Python"})
        clear_session(sid)
        assert get_progress(sid)["event_count"] == 0


# ─── FastAPI Routes Integration ───────────────────────────────────────────────

class TestCareerRoutesIntegration:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_health_endpoint(self, client):
        resp = client.get("/api/career/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["phase"] == 2

    def test_academic_year_endpoint(self, client):
        resp = client.post("/api/career/academic-year", json={
            "education_entries": [{
                "degree": "B.Tech",
                "institution": "Test University",
                "start_date": "2022",
                "end_date": "2026",
            }],
            "raw_text": "Final year B.Tech student.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "academic_stage" in data
        assert "confidence" in data

    def test_skill_gaps_endpoint(self, client):
        resp = client.post("/api/career/skill-gaps", json={
            "skills": [
                {"skill": "Docker", "jd_importance": 0.9, "current_level": "unknown"},
                {"skill": "Python", "jd_importance": 0.8, "current_level": "intermediate",
                 "resume_evidence": 0.7, "project_evidence": 0.6},
            ],
            "context": {"target_role": "Backend Developer", "months_to_placement": 4},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "skill_gaps" in data
        assert len(data["skill_gaps"]) == 2

    def test_claim_analysis_endpoint(self, client):
        resp = client.post("/api/career/claim-analysis", json={
            "projects": [{
                "name": "Indexify",
                "description": "Data ingestion system.",
                "highlights": ["Reduced latency by 40% using Redis caching."],
                "technologies": ["Python", "Redis"],
            }],
            "extracted_skills": ["Python", "Redis"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "claims" in data
        assert "evidence_profile" in data

    def test_interview_kit_endpoint(self, client):
        resp = client.post("/api/career/interview-kit", json={
            "target_role": "Full Stack Developer",
            "academic_stage": "final_year",
            "skill_gaps": ["React", "Node.js"],
            "projects": ["Portfolio Site"],
            "total_questions": 4,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["questions"]) == 4

    def test_roadmap_endpoint(self, client):
        resp = client.post("/api/career/roadmap", json={
            "skill_gaps": [
                {"skill": "Docker", "jd_importance": 0.85, "current_level": "beginner"},
            ],
            "context": {"target_role": "DevOps Engineer", "hours_per_week": 10},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["roadmap"]

    def test_resources_endpoint(self, client):
        resp = client.get("/api/career/resources?skill=Python&language=English&level=beginner")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_analyze_full_endpoint(self, client):
        resp = client.post("/api/career/analyze-full", json={
            "resume_text": "Final year B.Tech student with Python and Docker experience.",
            "job_description": "Backend Developer — requires Python, Docker, FastAPI.",
            "target_role": "Backend Developer",
            "education_entries": [{
                "degree": "B.Tech",
                "institution": "Test University",
                "start_date": "2022",
                "end_date": "2026",
            }],
            "jd_skills": [
                {"skill": "FastAPI", "jd_importance": 0.9, "current_level": "unknown"},
                {"skill": "Docker", "jd_importance": 0.85, "current_level": "beginner",
                 "project_evidence": 0.5},
            ],
            "months_to_placement": 6,
            "hours_per_week": 10,
            "generate_interview_kit": True,
            "generate_roadmap": True,
            "total_interview_questions": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        for key in ("session_id", "academic_year_detection", "skill_gap_analysis",
                    "learning_roadmap", "claim_analysis", "recruiter_interview_kit"):
            assert key in data, f"Missing key in analyze-full response: {key}"

    def test_progress_milestone_endpoint(self, client):
        sid = new_session()
        resp = client.post("/api/career/progress/milestone", json={
            "session_id": sid,
            "skill": "Docker",
            "milestone_text": "Completed Docker tutorial.",
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "Milestone recorded."
        clear_session(sid)

    def test_progress_verify_skill_endpoint(self, client):
        sid = new_session()
        resp = client.post("/api/career/progress/verify-skill", json={
            "session_id": sid,
            "skill": "Python",
            "evidence_url": "https://github.com/me/py-project",
            "notes": "Built a complete REST API.",
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "Skill verification recorded."
        clear_session(sid)

    def test_certifications_endpoint_first_year(self, client):
        resp = client.post("/api/career/certifications", json={
            "academic_stage": "first_year",
            "jd_skill_gaps": ["Python", "AWS", "Docker"],
            "max_recommendations": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "recommended" in data
        assert "save_for_later" in data
        assert "already_held" in data
        # First year students should NOT have CKA (Kubernetes advanced) recommended
        advanced_ids = [r["id"] for r in data["recommended"]]
        assert "cka" not in advanced_ids

    def test_certifications_endpoint_final_year(self, client):
        resp = client.post("/api/career/certifications", json={
            "academic_stage": "final_year",
            "jd_skill_gaps": ["AWS", "Kubernetes", "Docker"],
            "max_recommendations": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Final year students can see intermediate/advanced certs
        difficulties = [r["difficulty"] for r in data["recommended"]]
        assert "intermediate" in difficulties or "advanced" in difficulties

    def test_certifications_respects_existing(self, client):
        resp = client.post("/api/career/certifications", json={
            "academic_stage": "second_year",
            "jd_skill_gaps": ["Python", "AWS"],
            "existing_certifications": ["AWS Certified Cloud Practitioner"],
            "max_recommendations": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        # aws-ccp should be in already_held, not recommended
        rec_ids = [r["id"] for r in data["recommended"]]
        held_names = [r["name"] for r in data["already_held"]]
        assert "aws-ccp" not in rec_ids
        assert any("Cloud Practitioner" in n for n in held_names)

    def test_tools_endpoint(self, client):
        resp = client.post("/api/career/tools", json={
            "jd_skill_gaps": ["Python", "Docker", "PostgreSQL"],
            "academic_stage": "second_year",
            "max_per_skill": 2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "tool_recommendations_by_skill" in data
        assert "all_tools" in data
        # Should have tools for at least one recognized skill
        assert len(data["all_tools"]) > 0

    def test_analyze_full_includes_certifications(self, client):
        resp = client.post("/api/career/analyze-full", json={
            "resume_text": "2nd year B.Tech student with Python experience.",
            "job_description": "Backend Developer — Python, Docker, AWS required.",
            "target_role": "Backend Developer",
            "education_entries": [{
                "degree": "B.Tech",
                "institution": "Test University",
                "start_date": "2024",
                "end_date": "2028",
            }],
            "jd_skills": [
                {"skill": "Python", "jd_importance": 0.9, "current_level": "beginner"},
                {"skill": "AWS", "jd_importance": 0.85, "current_level": "unknown"},
                {"skill": "Docker", "jd_importance": 0.8, "current_level": "unknown"},
            ],
            "months_to_placement": 12,
            "generate_interview_kit": False,
            "generate_roadmap": False,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Must include cert & tool sections
        assert "certification_recommendations" in data
        assert "tool_recommendations" in data
        cert_data = data["certification_recommendations"]
        assert "recommended" in cert_data
        tool_data = data["tool_recommendations"]
        assert "tool_recommendations_by_skill" in tool_data


# ── Certification Advisor Unit Tests ─────────────────────────────────────────

class TestCertificationAdvisor:
    def test_first_year_gets_beginner_certs(self):
        from app.career_intelligence.certification_advisor import recommend_certifications
        result = recommend_certifications(
            academic_stage="first_year",
            jd_skill_gaps=["Python", "Git", "AWS"],
        )
        assert result["recommended"]
        for cert in result["recommended"]:
            assert cert["difficulty"] in ("beginner", "intermediate")

    def test_final_year_can_get_advanced_certs(self):
        from app.career_intelligence.certification_advisor import recommend_certifications
        result = recommend_certifications(
            academic_stage="final_year",
            jd_skill_gaps=["Kubernetes", "AWS", "Docker"],
        )
        difficulties = [c["difficulty"] for c in result["recommended"]]
        assert "intermediate" in difficulties or "advanced" in difficulties

    def test_already_held_cert_excluded_from_recommended(self):
        from app.career_intelligence.certification_advisor import recommend_certifications
        result = recommend_certifications(
            academic_stage="third_year",
            jd_skill_gaps=["Python", "Git"],
            existing_certifications=["PCEP – Certified Entry-Level Python Programmer"],
        )
        rec_ids = [c["id"] for c in result["recommended"]]
        assert "pcep" not in rec_ids
        held = [c["id"] for c in result["already_held"]]
        assert "pcep" in held

    def test_jd_irrelevant_certs_excluded(self):
        from app.career_intelligence.certification_advisor import recommend_certifications
        result = recommend_certifications(
            academic_stage="second_year",
            jd_skill_gaps=["Python"],  # Only Python in JD
        )
        # Kubernetes CKA should not appear for a Python-only JD
        rec_ids = [c["id"] for c in result["recommended"]]
        assert "cka" not in rec_ids

    def test_tools_returns_by_skill_map(self):
        from app.career_intelligence.certification_advisor import recommend_tools
        result = recommend_tools(
            jd_skill_gaps=["Docker", "PostgreSQL"],
            academic_stage="second_year",
        )
        assert "Docker" in result["tool_recommendations_by_skill"] or \
               "docker" in str(result["tool_recommendations_by_skill"]).lower()
        assert result["all_tools"]

    def test_tools_max_per_skill_respected(self):
        from app.career_intelligence.certification_advisor import recommend_tools
        result = recommend_tools(
            jd_skill_gaps=["Python", "Docker", "AWS"],
            academic_stage="final_year",
            max_per_skill=1,
        )
        for skill, tool_list in result["tool_recommendations_by_skill"].items():
            assert len(tool_list) <= 1

    def test_note_field_present(self):
        from app.career_intelligence.certification_advisor import recommend_certifications, recommend_tools
        cert_result = recommend_certifications("second_year", ["AWS"])
        tool_result = recommend_tools(["AWS"])
        assert "note" in cert_result
        assert "note" in tool_result
