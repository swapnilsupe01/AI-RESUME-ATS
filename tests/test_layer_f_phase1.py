from app.career_intelligence.schemas import SkillEvidence, CareerContext, Resource, ResourceQuery
from app.career_intelligence.skill_gap_engine import analyze_gaps
from app.career_intelligence.roadmap_generator import generate_roadmap
from app.career_intelligence.resource_ranker import rank_resources
from app.career_intelligence.interview_engine import start_interview, evaluate_answer
from app.career_intelligence.assessment_engine import create_assessment, score_assessment

def test_gaps_and_roadmap():
    context = CareerContext(target_role="Backend Developer", months_to_placement=4, hours_per_week=5)
    skills = [SkillEvidence(skill="AWS", jd_importance=.9, current_level="unknown"),
              SkillEvidence(skill="Python", jd_importance=.8, resume_evidence=.8, project_evidence=.8, current_level="intermediate")]
    ranked = analyze_gaps(skills, context)
    assert len(ranked) == 2
    assert ranked[0]["priority_score"] >= ranked[1]["priority_score"]
    assert generate_roadmap(skills, context)["roadmap"]

def test_resources():
    r = Resource(id="docker-docs", skill="Docker", title="Docker docs", url="https://docs.docker.com/",
                 language="English", source_type="official_docs", difficulty="beginner", hands_on=True, authority_score=1)
    result = rank_resources([r], ResourceQuery(skill="Docker", language="English"))
    assert result and result[0]["resource"]["id"] == "docker-docs"

def test_interview():
    session = start_interview("Backend Developer", "FastAPI", ["Resume API"], ["FastAPI"], "intermediate", 2)
    assert len(session["questions"]) == 2
    result = evaluate_answer("I reproduce issues, inspect logs, isolate the cause and verify the fix.", ["reproduce", "logs", "cause", "fix"])
    assert 0 <= result["score"] <= 100

def test_assessment():
    a = create_assessment("Docker", "beginner")
    result = score_assessment(a, {"q1": "An image is a template and a container is a running instance."}, True)
    assert 0 <= result["overall_score"] <= 100
