import uuid

BANK = [
    ("beginner", "Explain {skill} and the problem it solves.", ["definition", "use case", "limitation"]),
    ("intermediate", "How would you use {skill} in a {role} project?", ["design choice", "implementation", "trade-offs", "testing"]),
    ("intermediate", "A feature using {skill} fails. How would you investigate?", ["reproduce", "logs", "cause", "fix"]),
    ("advanced", "Discuss a scalability, reliability or security trade-off involving {skill}.", ["trade-off", "failure", "mitigation", "monitoring"]),
]

def start_interview(target_role, job_description, projects, skill_gaps, difficulty, count):
    skills = skill_gaps or [target_role]
    eligible = [q for q in BANK if difficulty == "advanced" or q[0] != "advanced"]
    questions = []
    for i in range(count):
        _, template, rubric = eligible[i % len(eligible)]
        skill = skills[i % len(skills)]
        questions.append({"question_id": str(uuid.uuid4()), "skill": skill,
                          "project_context": projects[i % len(projects)] if projects else None,
                          "question": template.format(skill=skill, role=target_role),
                          "rubric": rubric, "difficulty": difficulty})
    return {"session_id": str(uuid.uuid4()), "target_role": target_role,
            "questions": questions, "job_description_used": bool(job_description)}

def evaluate_answer(answer, rubric):
    lower = answer.lower()
    matched = [r for r in rubric if any(word in lower for word in r.lower().split())]
    length_score = min(1.0, len(answer.split()) / 80.0)
    coverage = len(matched) / max(len(rubric), 1)
    score = round(100 * (0.65 * coverage + 0.35 * length_score), 1)
    return {"score": score, "matched_rubric_items": matched,
            "feedback": "Use a concrete example and explain your reasoning and trade-offs.",
            "warning": "Keyword/length heuristic only; it does not establish technical correctness."}
