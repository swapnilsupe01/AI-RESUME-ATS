import uuid

BANK = {
    "docker": {
        "beginner": [{"id": "q1", "question": "Difference between image and container?", "expected": ["image", "container"]}],
        "intermediate": [{"id": "q1", "question": "How can a FastAPI image be reproducible and small?", "expected": ["dependencies", "multi-stage"]}],
        "advanced": [{"id": "q1", "question": "How would you secure and observe containers?", "expected": ["secrets", "health", "logs"]}]
    },
    "aws": {
        "beginner": [{"id": "q1", "question": "Why use least-privilege access?", "expected": ["permissions", "least privilege"]}],
        "intermediate": [{"id": "q1", "question": "How deploy an API without committing secrets?", "expected": ["deploy", "secrets"]}],
        "advanced": [{"id": "q1", "question": "How design a resilient, observable API?", "expected": ["availability", "monitoring"]}]
    }
}
def create_assessment(skill, level):
    questions = BANK.get(skill.lower(), {}).get(level, [{
        "id": "q1", "question": f"Explain a core concept and practical use of {skill}.",
        "expected": ["concept", "example"]
    }])
    return {"assessment_id": str(uuid.uuid4()), "skill": skill, "level": level, "questions": questions,
            "practical_task": f"Complete a small demonstrable task using {skill} and document how you tested it."}

def score_assessment(assessment, answers, completed_task):
    rows = []
    for q in assessment["questions"]:
        answer = answers.get(q["id"], "").lower()
        matched = [term for term in q["expected"] if term.lower() in answer]
        rows.append({"question_id": q["id"], "score": round(100 * len(matched) / max(len(q["expected"]), 1)),
                     "matched_concepts": matched, "missing_concepts": [x for x in q["expected"] if x not in matched]})
    quiz = round(sum(r["score"] for r in rows) / max(len(rows), 1))
    return {"quiz_score": quiz, "practical_task_completed": completed_task,
            "overall_score": round(0.7 * quiz + 30 * int(completed_task)), "question_results": rows,
            "warning": "Formative keyword-based score; review answers manually for important decisions."}
