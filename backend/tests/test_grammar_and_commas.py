# -*- coding: utf-8 -*-
"""
Regression test suite for grammar, unnecessary comma elimination, Oxford comma preservation,
parallel structure, and meaning-preserving validation in Layer E.
"""
import pytest
from app.generation.preservation_validator import (
    fix_unnecessary_commas,
    fix_parallel_infinitives,
    remove_resume_filler,
    clean_resume_sentence,
    is_already_strong_bullet,
    validate_suggestion_output,
)


def test_example_1_unnecessary_comma_compound_predicate():
    """
    Test Example 1 from user specification:
    Input: "Implemented isolated FastAPI sandbox execution using Docker, and deployed the full-stack application on Hugging Face Spaces."
    Expected: "Implemented isolated FastAPI sandbox execution using Docker and deployed the full-stack application on Hugging Face Spaces."
    """
    inp = "Implemented isolated FastAPI sandbox execution using Docker, and deployed the full-stack application on Hugging Face Spaces."
    expected = "Implemented isolated FastAPI sandbox execution using Docker and deployed the full-stack application on Hugging Face Spaces."

    # Direct comma cleaning
    cleaned = fix_unnecessary_commas(inp)
    assert cleaned == expected

    # Full sentence cleaning
    sentence_cleaned = clean_resume_sentence(inp)
    assert sentence_cleaned == expected

    # Validation pipeline
    val_text, is_valid, reason = validate_suggestion_output(
        original_text=inp,
        suggested_text=inp,
        content_type="WORK_EXPERIENCE",
        candidate_tools=["FastAPI", "Docker", "Hugging Face Spaces"],
    )
    assert val_text == expected
    assert is_valid is True


def test_example_2_parallel_infinitive_and_filler_reduction():
    """
    Test Example 2 from user specification:
    Input: "Conducted a comprehensive skill-gap analysis to identify matched and missing skills, and provided actionable resume recommendations."
    Expected: "Conducted a skill-gap analysis to identify matched and missing skills and provide actionable resume recommendations."
    """
    inp = "Conducted a comprehensive skill-gap analysis to identify matched and missing skills, and provided actionable resume recommendations."
    expected = "Conducted a skill-gap analysis to identify matched and missing skills and provide actionable resume recommendations."

    cleaned = clean_resume_sentence(inp)
    assert cleaned == expected

    val_text, is_valid, reason = validate_suggestion_output(
        original_text=inp,
        suggested_text=inp,
        content_type="WORK_EXPERIENCE",
        candidate_tools=[],
    )
    assert val_text == expected
    assert is_valid is True


def test_example_3_preserve_complex_list_with_oxford_comma():
    """
    Test Example 3 from user specification:
    Input: "Developed a Python SDK with callback tracing, HTML/JSON trace export, and a React interactive visualization studio."
    Expected: Preserve the original if the meaning is clear, without changing relationship between SDK features and visualization studio.
    """
    inp = "Developed a Python SDK with callback tracing, HTML/JSON trace export, and a React interactive visualization studio."

    # Oxford comma must be strictly preserved
    cleaned_commas = fix_unnecessary_commas(inp)
    assert cleaned_commas == inp
    assert ", and a React" in cleaned_commas

    # Sentence must be recognized as strong and correct
    assert is_already_strong_bullet(inp) is True

    # Validator must preserve the original without distortion
    val_text, is_valid, reason = validate_suggestion_output(
        original_text=inp,
        suggested_text=inp,
        content_type="PROJECT_DESCRIPTION",
        candidate_tools=["Python", "React", "HTML/JSON"],
    )
    assert val_text == inp
    assert is_valid is True
    assert ", and a React interactive visualization studio" in val_text


def test_example_4_preserve_valid_oxford_comma_list():
    """
    Test Example 4 from user specification:
    Input: "Built dashboards for analytics, reporting, and monitoring."
    Expected: Preserve the valid list and its commas.
    """
    inp = "Built dashboards for analytics, reporting, and monitoring."

    cleaned_commas = fix_unnecessary_commas(inp)
    assert cleaned_commas == inp
    assert ", and monitoring" in cleaned_commas

    val_text, is_valid, reason = validate_suggestion_output(
        original_text=inp,
        suggested_text=inp,
        content_type="WORK_EXPERIENCE",
        candidate_tools=[],
    )
    assert val_text == inp
    assert is_valid is True
    assert ", and monitoring." in val_text


def test_introductory_clause_with_compound_predicate():
    """
    Introductory clause + 2 coordinated verbs:
    Input: "Using Docker and Nginx, containerized the backend services, and deployed them to AWS."
    Expected: "Using Docker and Nginx, containerized the backend services and deployed them to AWS."
    The comma after Nginx (introductory) is kept; the comma before 'and deployed' is removed.
    """
    inp = "Using Docker and Nginx, containerized the backend services, and deployed them to AWS."
    expected = "Using Docker and Nginx, containerized the backend services and deployed them to AWS."

    cleaned = fix_unnecessary_commas(inp)
    assert cleaned == expected
    assert "Using Docker and Nginx," in cleaned
    assert "backend services and deployed" in cleaned


def test_three_verb_oxford_comma_list_preserved():
    """
    A 3-item list of verbs:
    Input: "Architected the database schema, engineered the FastAPI backend, and deployed the application using Docker."
    Expected: Oxford comma before 'and deployed' is preserved because there are 3 parallel actions.
    """
    inp = "Architected the database schema, engineered the FastAPI backend, and deployed the application using Docker."

    cleaned = fix_unnecessary_commas(inp)
    assert cleaned == inp
    assert ", and deployed" in cleaned


def test_independent_clauses_with_subjects_preserved():
    """
    Two independent clauses with distinct subjects:
    Input: "The API processed 50,000 requests per minute, and the database automatically scaled down during off-peak hours."
    Expected: Comma before 'and' is preserved because both clauses have their own grammatical subjects.
    """
    inp = "The API processed 50,000 requests per minute, and the database automatically scaled down during off-peak hours."

    cleaned = fix_unnecessary_commas(inp)
    assert cleaned == inp
    assert ", and the database" in cleaned


def test_technical_entities_strictly_preserved():
    """
    Ensure technical tools are never dropped during validation.
    """
    orig = "Built an AI resume intelligence platform using Python, FastAPI, ChromaDB, and Sentence-BERT."
    sugg_dropped = "Built an AI resume intelligence platform using Python and web frameworks."

    val_text, is_valid, reason = validate_suggestion_output(
        original_text=orig,
        suggested_text=sugg_dropped,
        content_type="PROJECT_DESCRIPTION",
        candidate_tools=["Python", "FastAPI", "ChromaDB", "Sentence-BERT"],
    )
    # Must reject suggestion that dropped critical technologies
    assert is_valid is False
    assert "FastAPI" in val_text
    assert "ChromaDB" in val_text


def test_unsupported_verb_injection_rejected():
    """
    Ensure the validator rejects when the AI tries to inject unsupported action verbs
    (like 'deployed', 'led', 'managed') that were not in the candidate's original text.
    """
    orig = "Built REST APIs using FastAPI and ChromaDB."
    sugg_invented = "Built REST APIs using FastAPI and ChromaDB, and deployed the application to Kubernetes."

    val_text, is_valid, reason = validate_suggestion_output(
        original_text=orig,
        suggested_text=sugg_invented,
        content_type="WORK_EXPERIENCE",
        candidate_tools=["FastAPI", "ChromaDB"],
    )
    # Must reject invented deployment claim
    assert is_valid is False
    assert "Kubernetes" not in val_text or "deployed" not in val_text
