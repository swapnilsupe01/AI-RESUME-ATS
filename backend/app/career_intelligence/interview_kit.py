"""
Recruiter Interview Kit for Layer F — AI Career Intelligence Engine.
Generates multi-tier, stage-adapted probing questions spanning 10 recruiter categories,
linked to actual resume claims, skill gaps, and project evidence.
"""

import uuid
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

from .claim_analyzer import ResumeClaim
from .academic_year_detector import AcademicStage


QuestionCategory = Literal[
    "claim_verification",
    "project_ownership",
    "technical_concepts",
    "architecture_design",
    "debugging_failure_analysis",
    "testing_deployment",
    "security_reliability_performance",
    "design_tradeoffs",
    "job_description_gaps",
    "placement_readiness"
]


class InterviewQuestion(BaseModel):
    question_id: str = Field(default_factory=lambda: f"q_{uuid.uuid4().hex[:8]}")
    question_text: str
    category: QuestionCategory
    difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    target_academic_stages: List[AcademicStage] = Field(default_factory=list)
    related_claim: Optional[str] = None
    related_skill: Optional[str] = None
    project_context: Optional[str] = None
    recruiter_intent: str = ""
    rubric_criteria: List[str] = Field(default_factory=list)
    sample_strong_points: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    suggested_action: Optional[str] = None


# Curated question templates mapped to categories and academic stages
STAGE_QUESTION_BANK = [
    # 1. Technical Concepts (Stage: First & Second Year)
    {
        "category": "technical_concepts",
        "difficulty": "beginner",
        "stages": ["first_year", "second_year", "third_year"],
        "template": "Explain how {skill} works under the hood and what real-world problem it solves in {role} development.",
        "intent": "Assesses foundational clarity and ability to explain core technical abstractions without buzzwords.",
        "rubric": ["core definition", "underlying mechanism", "primary use case", "common pitfall"],
        "strong_points": [
            "Clearly defines the technology without relying on memorized buzzwords.",
            "Contrasts it with simple alternatives or predecessor tools.",
            "Explains practical advantages in real development workflows."
        ],
        "follow_ups": [
            "What happens if you don't use {skill} and build it from scratch?",
            "Can you give an example of when {skill} is the wrong tool for the job?"
        ],
        "action": "Review core documentation and build a minimal standalone prototype demonstrating {skill}."
    },
    # 2. Project Ownership & Individual Contribution (All stages)
    {
        "category": "project_ownership",
        "difficulty": "intermediate",
        "stages": ["first_year", "second_year", "third_year", "final_year", "graduated"],
        "template": "In your project '{project}', what specific modules or lines of logic did you personally design and write versus third-party libraries or boilerplate?",
        "intent": "Separates genuine individual hands-on coding contribution from cloned repositories, tutorial followers, or team work.",
        "rubric": ["exact personal contribution", "architectural ownership", "challenges solved individually", "library vs custom code"],
        "strong_points": [
            "Directly articulates the specific components they built (e.g. state management, API routes, database schema).",
            "Transparently explains which open-source packages were integrated.",
            "Walks through specific tricky edge cases encountered during personal coding."
        ],
        "follow_ups": [
            "If I open your GitHub commit history for '{project}', what are the most complex pull requests authored by you?",
            "If you had another 2 weeks on '{project}', what technical debt would you refactor?"
        ],
        "action": "Prepare a 2-minute architectural walkthrough of '{project}' focusing on your custom data structures and algorithms."
    },
    # 3. Architecture & Design Decisions (Stage: Third Year, Final Year, Grad)
    {
        "category": "architecture_design",
        "difficulty": "advanced",
        "stages": ["third_year", "final_year", "graduated"],
        "template": "How did you design the communication and data flow in '{project}'? Why did you select this specific architecture over alternative patterns?",
        "intent": "Evaluates architectural maturity, component decoupling, data flow design, and reasoning behind architectural choices.",
        "rubric": ["data flow diagrams", "separation of concerns", "state/data persistence", "architectural alternative evaluation"],
        "strong_points": [
            "Explains client-server or service boundaries clearly.",
            "Justifies why a simpler or more complex architecture was chosen for the problem scale.",
            "Details how data flows from request ingress to persistence."
        ],
        "follow_ups": [
            "How does your architecture handle unexpected surges in concurrent requests?",
            "Where is the state stored, and how would you make this service horizontally scalable?"
        ],
        "action": "Sketch the component interaction and database relationship diagram for '{project}'."
    },
    # 4. Debugging & Failure Analysis (Stage: Second Year, Third Year, Final Year, Grad)
    {
        "category": "debugging_failure_analysis",
        "difficulty": "intermediate",
        "stages": ["second_year", "third_year", "final_year", "graduated"],
        "template": "Walk me through the single hardest bug or unexpected runtime failure you encountered while using {skill} in '{project}'. How did you isolate and fix it?",
        "intent": "Probes real-world problem-solving, root cause analysis methodologies, and troubleshooting resilience.",
        "rubric": ["failure symptom", "systematic reproduction", "profiling/logging tools used", "root cause identification", "permanent fix and regression test"],
        "strong_points": [
            "Describes a systematic debugging methodology rather than trial-and-error guessing.",
            "Explains tools used (stack traces, logging, breakpoints, network inspect).",
            "Highlights how the bug was verified fixed and prevented from reoccurring."
        ],
        "follow_ups": [
            "What automated test could you write to ensure this bug never returns?",
            "How did that bug change how you structure your code in subsequent projects?"
        ],
        "action": "Document your top 3 project debugging war stories with reproduction steps and root causes."
    },
    # 5. Testing & Deployment (Stage: Third Year, Final Year, Grad)
    {
        "category": "testing_deployment",
        "difficulty": "intermediate",
        "stages": ["third_year", "final_year", "graduated"],
        "template": "How do you test and deploy applications built with {skill}? How do you ensure regression safety before pushing to production?",
        "intent": "Checks software engineering hygiene, test pyramid awareness, CI/CD knowledge, and deployment confidence.",
        "rubric": ["unit vs integration testing", "mocking external dependencies", "CI automation", "environment parity"],
        "strong_points": [
            "Distinguishes between unit tests, integration tests, and end-to-end tests.",
            "Explains how environment variables and secrets are handled securely.",
            "Mentions CI pipelines (like GitHub Actions) and containerized workflows."
        ],
        "follow_ups": [
            "How do you mock or stub external API services or databases in your test suite?",
            "What happens if a deployment fails midway? What is your rollback strategy?"
        ],
        "action": "Set up an automated GitHub Actions CI workflow running unit tests with coverage reporting."
    },
    # 6. Security, Reliability & Performance (Stage: Final Year, Grad)
    {
        "category": "security_reliability_performance",
        "difficulty": "advanced",
        "stages": ["third_year", "final_year", "graduated"],
        "template": "What security vulnerabilities or performance bottlenecks are most common when utilizing {skill}, and how do you protect against them?",
        "intent": "Determines if the candidate understands production hardening, OWASP security principles, and computational complexity.",
        "rubric": ["injection/auth vulnerability mitigation", "indexing and latency optimization", "rate limiting & DoS defense", "memory/resource management"],
        "strong_points": [
            "Identifies specific security risks (e.g. SQL injection, CORS, broken object level authorization).",
            "Explains concrete mitigations (parameterized queries, token hashing, input validation schemas).",
            "Discusses performance optimization through algorithmic complexity and caching."
        ],
        "follow_ups": [
            "How do you protect your API endpoints from brute-force authentication attacks or scraping?",
            "How do you profile memory leaks or slow query execution in production?"
        ],
        "action": "Run a security audit (e.g. OWASP Top 10 checklist) and latency profiling on your primary project."
    },
    # 7. Design Trade-Offs (Stage: Third Year, Final Year, Grad)
    {
        "category": "design_tradeoffs",
        "difficulty": "advanced",
        "stages": ["third_year", "final_year", "graduated"],
        "template": "Every engineering choice has trade-offs. What was the biggest technical compromise you accepted when choosing {skill} for your system?",
        "intent": "Identifies engineering pragmatism and depth. Senior engineers recognize that every tool comes with costs and trade-offs.",
        "rubric": ["pros vs cons analysis", "operational complexity", "learning curve vs performance", "justification of compromise"],
        "strong_points": [
            "Does not portray any technology as a magic silver bullet.",
            "Clearly states what was sacrificed (e.g. development speed vs runtime speed, operational complexity vs flexibility).",
            "Explains why the trade-off was acceptable given the project's specific constraints."
        ],
        "follow_ups": [
            "At what scale or user volume would that decision become an operational bottleneck?",
            "If you had infinite cloud budget or time, would you still make that same choice?"
        ],
        "action": "Write an Architecture Decision Record (ADR) detailing the trade-offs of your tech stack."
    },
    # 8. Job-Description Skill Gaps (All stages)
    {
        "category": "job_description_gaps",
        "difficulty": "intermediate",
        "stages": ["first_year", "second_year", "third_year", "final_year", "graduated"],
        "template": "The target {role} role lists {skill} as a key requirement, but your resume has limited direct evidence. How quickly can you bridge this gap and how would you ramp up?",
        "intent": "Evaluates self-awareness, technical agility, learning methodology, and transferable conceptual knowledge.",
        "rubric": ["transferable concepts from known tools", "rapid learning plan", "hands-on proof of concept plan", "honest assessment of familiarity"],
        "strong_points": [
            "Demonstrates awareness of how concepts from tools they know transfer directly to {skill}.",
            "Outlines a disciplined 1-2 week learning plan with a practical deliverable.",
            "Projects confidence grounded in fundamental computer science principles."
        ],
        "follow_ups": [
            "What analogous concepts in languages or frameworks you already know apply to {skill}?",
            "What small project would you build over a weekend to prove basic competence to our team?"
        ],
        "action": "Complete a 3-day guided project targeting {skill} and push it to a public GitHub repository."
    },
    # 9. Placement & Internship Readiness (Stage: First, Second, Third Year)
    {
        "category": "placement_readiness",
        "difficulty": "beginner",
        "stages": ["first_year", "second_year", "third_year", "final_year"],
        "template": "As a {stage} student aiming for a {role} position, how do your academic coursework and hands-on projects prepare you for Day 1 on a production engineering team?",
        "intent": "Assesses professionalism, adaptability, teamwork expectations, and transition readiness from college to industry.",
        "rubric": ["coursework application", "git & collaborative development", "eagerness to learn", "independent problem solving"],
        "strong_points": [
            "Connects theoretical university courses (DSA, DBMS, OS, Networks) to real programming practice.",
            "Demonstrates familiarity with version control workflows and PR reviews.",
            "Expresses enthusiasm and a proactive approach to receiving mentorship."
        ],
        "follow_ups": [
            "How do you handle receiving critical code review feedback from senior engineers?",
            "Describe a time you had to learn a completely unfamiliar library in 48 hours."
        ],
        "action": "Practice explaining university computer science fundamentals in terms of industry software engineering applications."
    }
]


def generate_interview_kit(
    target_role: str = "Software Developer",
    academic_stage: AcademicStage = "final_year",
    claims: Optional[List[ResumeClaim]] = None,
    skill_gaps: Optional[List[str]] = None,
    projects: Optional[List[str]] = None,
    target_count: int = 8
) -> Dict[str, Any]:
    """
    Generate a comprehensive, stage-adapted Recruiter Interview Kit.
    Integrates resume-claim probing, skill gaps, and stage-specific questions.
    """
    questions: List[InterviewQuestion] = []
    seen_texts = set()

    stage_display = academic_stage.replace("_", " ").title()
    cand_claims = claims or []
    cand_gaps = skill_gaps or []
    cand_projs = projects or ["Main Project"]

    # 1. Category 1: Resume-Claim Probing Questions (Directly from parsed claims)
    for claim in cand_claims:
        if len(questions) >= target_count // 2:
            break
            
        probing_qs = claim.suggested_probing_questions
        for q_text in probing_qs:
            if q_text not in seen_texts:
                seen_texts.add(q_text)
                
                # Determine difficulty and intent based on claim status
                diff: Literal["beginner", "intermediate", "advanced"] = "intermediate"
                if claim.metrics_claimed or claim.category in ("architecture_scale", "security_auth"):
                    diff = "advanced"
                elif claim.category == "general_technical":
                    diff = "beginner" if academic_stage in ("first_year", "second_year") else "intermediate"

                intent = (
                    f"Recruiter Probing: Candidate claimed '{claim.text[:80]}...' in {claim.source_title or 'resume'}. "
                    f"Evidence status: {claim.evidence_status.replace('_', ' ')}. Verifies technical depth and baseline measurement."
                )

                questions.append(
                    InterviewQuestion(
                        question_text=q_text,
                        category="claim_verification",
                        difficulty=diff,
                        target_academic_stages=[academic_stage],
                        related_claim=claim.text,
                        related_skill=claim.related_skills[0] if claim.related_skills else None,
                        project_context=claim.source_title or None,
                        recruiter_intent=intent,
                        rubric_criteria=[
                            "accurate technical terminology",
                            "specific metrics / baseline explanation",
                            "individual contribution clarity",
                            "engineering trade-offs"
                        ],
                        sample_strong_points=[
                            "Explains the exact technical mechanism used to fulfill the resume claim.",
                            "Shares authentic metrics, constraints, and profiling tools used.",
                            "Distinguishes between personal implementation and existing library code."
                        ],
                        follow_up_questions=[
                            f"What was the most difficult architectural compromise in {claim.source_title or 'this work'}?",
                            "How would you refactor this implementation if you had to support 100x user scale?"
                        ],
                        suggested_action=f"Review the implementation details and telemetry of your '{claim.source_title or 'project'}' claim."
                    )
                )
                break

    # 2. Category 2: Skill-Gap Probing Questions
    for gap in cand_gaps:
        if len(questions) >= target_count - 2:
            break
        q_text = f"The target {target_role} role requires {gap}, which is currently an identified skill gap. How would you quickly master this and build a functional prototype?"
        if q_text not in seen_texts:
            seen_texts.add(q_text)
            questions.append(
                InterviewQuestion(
                    question_text=q_text,
                    category="job_description_gaps",
                    difficulty="intermediate",
                    target_academic_stages=[academic_stage],
                    related_skill=gap,
                    recruiter_intent=f"Tests candidate self-learning ability and conceptual foundations for {gap}.",
                    rubric_criteria=["rapid learning plan", "transferable knowledge", "practical prototype idea"],
                    sample_strong_points=[
                        f"Identifies how fundamental software concepts map to {gap}.",
                        "Proposes a concrete 1-2 week hands-on learning project."
                    ],
                    follow_up_questions=[
                        f"What tools in your existing skill set share similarities with {gap}?",
                        f"What official documentation or resources would you consult first for {gap}?"
                    ],
                    suggested_action=f"Follow the Layer F Roadmap milestone for {gap}."
                )
            )

    # 3. Category 3: Stage-Adapted Questions from Bank
    available_templates = [
        item for item in STAGE_QUESTION_BANK
        if academic_stage in item["stages"] or "first_year" in item["stages"]
    ]

    skill_cycle = cand_gaps or ["Software Engineering"]
    proj_cycle = cand_projs or ["Portfolio Project"]

    for idx, tpl in enumerate(available_templates):
        if len(questions) >= target_count:
            break
        
        skill = skill_cycle[idx % len(skill_cycle)]
        proj = proj_cycle[idx % len(proj_cycle)]
        
        formatted_q = tpl["template"].format(
            skill=skill,
            role=target_role,
            project=proj,
            stage=stage_display
        )
        
        if formatted_q not in seen_texts:
            seen_texts.add(formatted_q)
            questions.append(
                InterviewQuestion(
                    question_text=formatted_q,
                    category=tpl["category"],  # type: ignore
                    difficulty=tpl["difficulty"],  # type: ignore
                    target_academic_stages=tpl["stages"],  # type: ignore
                    related_skill=skill,
                    project_context=proj,
                    recruiter_intent=tpl["intent"],
                    rubric_criteria=tpl["rubric"],
                    sample_strong_points=tpl["strong_points"],
                    follow_up_questions=tpl["follow_ups"],
                    suggested_action=tpl["action"].format(skill=skill, project=proj) if "{skill}" in tpl["action"] else tpl["action"]
                )
            )

    return {
        "target_role": target_role,
        "academic_stage": academic_stage,
        "total_questions": len(questions),
        "questions": [q.model_dump() for q in questions],
        "stage_adaptation_note": (
            f"Questions automatically calibrated for {stage_display} candidates. "
            f"Focuses on practical concepts, genuine project ownership, and evidence-backed claims."
        )
    }
