"""
Tests for AI Resume ATS Suggestion Engine — Content Preservation and Content-Type Classification.
Verifies all requirements (Test A through Test G) specified in the task.
"""
from app.generation.content_classifier import classify_content_type
from app.generation.preservation_validator import (
    validate_suggestion_output,
    format_tech_stack,
    validate_and_preserve,
)
from app.generation.suggestion_manager import (
    Suggestion,
    UpgradeSession,
)


def test_test_a_technology_stack():
    """
    Test A: Technology Stack
    Input: React, FastAPI, Python, Ollama, Llama 3.2, Docker, OWASP Juice Shop
    Expected: Remains a technology stack with every original tech, never converted to narrative description.
    """
    raw_input = "React, FastAPI, Python, Ollama, Llama 3.2, Docker, OWASP Juice Shop"
    cat = classify_content_type(raw_input)
    assert cat in ("TECH_STACK", "SKILLS")

    # Format tech stack
    formatted = format_tech_stack(raw_input)
    # Validate output
    final_text, valid, reason = validate_suggestion_output(raw_input, formatted, cat)
    assert valid is True
    for item in ["React", "FastAPI", "Python", "Ollama", "Llama 3.2", "Docker", "OWASP Juice Shop"]:
        assert item.lower() in final_text.lower()

    # Reject hallucinated narrative description
    hallucinated = (
        "Developed a secure web application using React for the frontend and FastAPI for the backend, "
        "leveraging Python and integrating with Ollama and Llama 3.2 to enhance user experience, and "
        "deployed the application on Docker, while also participating in a simulated OWASP Juice Shop "
        "to identify vulnerabilities and improve security."
    )
    fallback_text, valid, reason = validate_suggestion_output(raw_input, hallucinated, cat)
    assert valid is False
    # Should fallback to preserved original/formatted stack
    assert "React" in fallback_text and "FastAPI" in fallback_text
    assert "Developed a secure" not in fallback_text


def test_test_b_project_description():
    """
    Test B: Project Description
    Input: Developed a full-stack vulnerability scanning and intelligence platform for OWASP Juice Shop.
    Expected: AI may improve wording but must not invent technologies or implementation details.
    """
    raw_input = "Developed a full-stack vulnerability scanning and intelligence platform for OWASP Juice Shop."
    cat = classify_content_type(raw_input)
    assert cat in ("PROJECT_DESCRIPTION", "WORK_EXPERIENCE", "RESPONSIBILITY")

    # Good improvement preserving context
    good_suggestion = "Engineered a full-stack vulnerability scanning and intelligence platform for OWASP Juice Shop."
    final_text, valid, reason = validate_suggestion_output(raw_input, good_suggestion, cat)
    assert valid is True
    assert "OWASP Juice Shop" in final_text


def test_test_c_project_description_with_technology_stack():
    """
    Test C: Project Description With Technology Stack
    Input: Built an AI resume analyzer using Python, FastAPI, and Sentence-BERT.
    Expected: Suggestion retains Python, FastAPI, and Sentence-BERT, improving wording only when useful.
    """
    raw_input = "Built an AI resume analyzer using Python, FastAPI, and Sentence-BERT."
    cat = classify_content_type(raw_input)
    assert cat in ("PROJECT_DESCRIPTION", "WORK_EXPERIENCE")

    improved = "Engineered an AI resume analyzer utilizing Python, FastAPI, and Sentence-BERT."
    final_text, valid, reason = validate_suggestion_output(raw_input, improved, cat)
    assert valid is True
    for tech in ["Python", "FastAPI", "Sentence-BERT"]:
        assert tech.lower() in final_text.lower()


def test_test_d_work_experience():
    """
    Test D: Work Experience
    Input: Worked on backend APIs and fixed bugs in the application.
    Expected: AI may improve grammar/phrasing without inventing leadership, metrics, or extra tools.
    """
    raw_input = "Worked on backend APIs and fixed bugs in the application."
    cat = classify_content_type(raw_input)
    assert cat in ("WORK_EXPERIENCE", "RESPONSIBILITY", "PROJECT_DESCRIPTION")

    improved = "Engineered backend APIs and resolved system bugs to enhance application reliability."
    final_text, valid, reason = validate_suggestion_output(raw_input, improved, cat)
    assert valid is True


def test_test_e_achievement():
    """
    Test E: Achievement
    Input: Improved model accuracy from 82% to 91%.
    Expected: Preserves exact original metrics (82% and 91%) without inventing numbers.
    """
    raw_input = "Improved model accuracy from 82% to 91%."
    cat = classify_content_type(raw_input)
    assert cat == "ACHIEVEMENT"

    improved = "Elevated model accuracy from 82% to 91% through targeted hyperparameter tuning."
    final_text, valid, reason = validate_suggestion_output(raw_input, improved, cat)
    assert valid is True
    assert "82%" in final_text and "91%" in final_text

    # Hallucinated different metrics
    corrupted = "Elevated model accuracy from 70% to 99%."
    fallback, valid, reason = validate_suggestion_output(raw_input, corrupted, cat)
    assert valid is False
    assert fallback == raw_input


def test_test_f_ambiguous_input():
    """
    Test F: Ambiguous Input
    Input: Python, Docker, deployment, APIs
    Expected: The AI must not invent a project description or assume what was implemented.
    """
    raw_input = "Python, Docker, deployment, APIs"
    cat = classify_content_type(raw_input)
    assert cat in ("TECH_STACK", "SKILLS", "OTHER")

    # If treated as tech stack, it must not become a narrative sentence
    formatted = format_tech_stack(raw_input)
    final_text, valid, reason = validate_suggestion_output(raw_input, formatted, cat)
    assert valid is True
    assert "Built an enterprise" not in final_text
    assert "Python" in final_text and "Docker" in final_text


def test_test_g_accept_and_reject_workflow():
    """
    Test G: Accept and Reject
    Verify that accepting a suggestion updates only the intended resume field and rejecting it
    leaves the original CV content unchanged. Also verify custom edit override.
    """
    # Create a suggestion
    orig_text = "React, FastAPI, Python, Ollama, Llama 3.2, Docker, OWASP Juice Shop"
    sug_text = "React, FastAPI, Python, Ollama, Llama 3.2, Docker, OWASP Juice Shop"
    sug = Suggestion(
        section="projects",
        item_id="proj_1",
        field="tech_stack",
        original_text=orig_text,
        suggested_text=sug_text,
        explanation="The original technology stack is already clear. Preserved all items.",
        category="TECH_STACK",
    )

    # Initial state
    assert sug.status == "pending"
    assert sug.original_text == orig_text
    assert sug.suggested_text == sug_text
    assert sug.edited_text == ""
    d = sug.to_dict()
    assert d["accepted_text"] == ""
    assert d["resolved_text"] == orig_text

    # Test Rejection
    sess = UpgradeSession(
        canonical_resume={"projects": [{"id": "proj_1", "tech_stack": orig_text}]},
        session_id="test_sess_1"
    )
    sess.add_suggestion(sug)

    sess.reject(sug.id)
    assert sug.status == "rejected"
    assert sug.original_text == orig_text  # Untouched
    d_rej = sug.to_dict()
    assert d_rej["status"] == "rejected"
    assert d_rej["resolved_text"] == orig_text

    # Reset and test Acceptance with Custom Override
    sug2 = Suggestion(
        section="projects",
        item_id="proj_1",
        field="tech_stack",
        original_text=orig_text,
        suggested_text=sug_text,
        explanation="The original technology stack is already clear.",
        category="TECH_STACK",
    )
    sess2 = UpgradeSession(
        canonical_resume={"projects": [{"id": "proj_1", "tech_stack": orig_text}]},
        session_id="test_sess_2"
    )
    sess2.add_suggestion(sug2)

    custom_override_val = "React, FastAPI, Python 3.11, Ollama, Llama 3.2, Docker"
    sess2.accept(sug2.id, edited_text=custom_override_val)

    assert sug2.status == "accepted"
    assert sug2.original_text == orig_text  # Untouched
    assert sug2.edited_text == custom_override_val
    d_acc = sug2.to_dict()
    assert d_acc["custom_override"] == custom_override_val
    assert d_acc["accepted_text"] == custom_override_val
    assert d_acc["resolved_text"] == custom_override_val

