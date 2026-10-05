"""
Unit tests for validator.py and rewrite_with_validation pipeline.
Covers:
- Known edge cases: sentence-ending period, unicode non-breaking hyphen, Oxford comma counting
- Mocked call_llm generation limits (call_count <= max_retries + 1)
- Best candidate selection (fewest issues)
- Valid first draft (retries=0, no correction call)
- Status field assertions ("passed_heuristic_checks" / "verified_by_heuristics" vs "needs_review")
- Qwen error handling: ReadTimeout retried once; 401/402/invalid-model raise immediately
"""
import pytest
from unittest.mock import MagicMock
from validator import (
    validate,
    split_sentences,
    count_separators,
    new_terms,
    missing_keywords,
    build_prompt,
    rewrite_with_validation,
    MAX_WORDS,
    MAX_SEPARATORS,
)


# ── Edge Case Tests (Requirement 11) ──────────────────────────────────────────

def test_edge_case_sentence_ending_period():
    """
    Sentence-ending period vs bare word:
    Proposed has 'deployment.' at the end of sentence; original has 'deployment'.
    The period is sentence punctuation and must NOT be flagged as a new term.
    """
    original = "Experienced in software deployment and testing."
    proposed = "Computer Engineering student skilled in software deployment."
    
    # Should not flag 'deployment.' as a new term
    terms = new_terms(original, proposed)
    assert "deployment." not in terms
    assert "deployment" not in terms


def test_edge_case_unicode_non_breaking_hyphen():
    """
    Unicode non-breaking hyphen vs ASCII hyphen:
    Proposed has 'hands‑on' (Unicode \u2011); original has 'hands-on' (ASCII \u002d).
    Should normalize and match without flagging 'hands' or 'on' as a new term.
    """
    original = "Hands-on experience in cloud systems."
    proposed = "Hands\u2011on experience in cloud systems."  # \u2011 non-breaking hyphen

    terms = new_terms(original, proposed)
    assert "hands" not in terms
    assert "on" not in terms
    assert len(terms) == 0


def test_edge_case_oxford_comma_separator_counting():
    """
    ', and' (Oxford comma) separator counting:
    In a 3-item list 'A, B, and C', there are 2 item separators.
    ', and' must be counted as 1 delimiter, not 2 (comma + and).
    """
    sentence = "Skills include Python, FastAPI, and PostgreSQL."
    # 2 list separators: comma after Python, ', and' before PostgreSQL
    assert count_separators(sentence) == 2

    # A 4-item list with Oxford comma and introductory clause
    sentence_4 = "In engineering, tools include Python, FastAPI, Docker, and PostgreSQL."
    # 4 separators total: 1 introductory comma, 2 list commas, 1 ', and'
    assert count_separators(sentence_4) == 4
    assert count_separators(sentence_4) <= MAX_SEPARATORS


# ── Mocked Pipeline Tests (Requirement 10 & 12) ──────────────────────────────

def test_valid_first_draft_retries_zero():
    """Valid first draft returns retries=0 with no correction call."""
    original = "Computer Engineering student with experience in Python and FastAPI."
    clean_draft = "Computer Engineering student with experience in Python and FastAPI."

    mock_llm = MagicMock(return_value=clean_draft)
    result = rewrite_with_validation(mock_llm, original, keywords=["Python", "FastAPI"], max_retries=2)

    assert result["retries_used"] == 0
    assert result["summary"] == clean_draft
    assert result["issues"] == []
    assert result["status"] == "passed_heuristic_checks"
    assert result["status"] == "verified_by_heuristics"
    assert mock_llm.call_count == 1  # Only 1 initial call, no correction call


def test_total_generations_never_exceed_max_retries_plus_one():
    """Assert call count never exceeds max_retries + 1."""
    original = "Computer Engineering student with experience in Python."
    # Draft with a persistent hallucinated term to force all retries
    bad_draft = "Computer Engineering student with experience in Python and Kubernetes and Docker and Jenkins and AWS and Azure and GCP and Terraform."

    mock_llm = MagicMock(return_value=bad_draft)
    max_retries = 2
    result = rewrite_with_validation(mock_llm, original, max_retries=max_retries)

    assert mock_llm.call_count == max_retries + 1  # 1 initial + 2 retries = 3 calls
    assert result["retries_used"] == max_retries
    assert len(result["issues"]) > 0
    assert result["status"] == "needs_review"


def test_best_candidate_returned_not_last_draft():
    """Best candidate (fewest issues) is returned, not the last draft."""
    original = "Computer Engineering student experienced in Python, FastAPI, and Docker."
    
    # Draft 1: 3 issues (too long, overloaded, new term)
    draft_1 = "Computer Engineering student experienced in Python, FastAPI, Docker, Kubernetes, Jenkins, Terraform, AWS, Azure, GCP, and Ansible with ten years of enterprise development experience across multiple large scale distributed systems."
    # Draft 2: 1 issue (minor new term 'blockchain')
    draft_2 = "Computer Engineering student experienced in Python, FastAPI, Docker, and blockchain."
    # Draft 3: 2 issues (new terms 'blockchain' and 'kubernetes')
    draft_3 = "Computer Engineering student experienced in Python, FastAPI, Docker, blockchain, and kubernetes."

    mock_llm = MagicMock(side_effect=[draft_1, draft_2, draft_3])
    result = rewrite_with_validation(mock_llm, original, max_retries=2)

    assert mock_llm.call_count == 3
    # Draft 2 had 1 issue while Draft 3 had 2 issues. Best draft (Draft 2) must be returned!
    assert result["summary"] == draft_2
    assert len(result["issues"]) == 1
    assert result["status"] == "needs_review"


def test_status_field_values():
    """Verify status is passed_heuristic_checks/verified_by_heuristics on success, needs_review on failure."""
    original = "Python developer."
    valid_draft = "Python developer."
    result_ok = rewrite_with_validation(MagicMock(return_value=valid_draft), original)
    assert result_ok["status"] in ("passed_heuristic_checks", "verified_by_heuristics")
    assert result_ok["status"] != "needs_review"
    assert result_ok["status"] != "verified"  # Requirement 12: never label "verified"

    invalid_draft = "Quantum astronaut with zero Python."
    result_fail = rewrite_with_validation(MagicMock(return_value=invalid_draft), original, max_retries=1)
    assert result_fail["status"] == "needs_review"


# ── Qwen Error Handling Tests (Requirement 10) ───────────────────────────────

def test_qwen_readtimeout_retried_once():
    """Qwen: ReadTimeout is retried exactly once."""
    from test_llm_providers import call_qwen_with_client

    mock_client = MagicMock()
    # First call raises ReadTimeout; second call succeeds
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="Rewritten summary text."))]
    mock_client.chat.completions.create.side_effect = [
        TimeoutError("Read timed out"),
        mock_resp,
    ]

    result = call_qwen_with_client(mock_client, "test-model", "Test prompt")
    assert result == "Rewritten summary text."
    assert mock_client.chat.completions.create.call_count == 2


def test_qwen_non_retryable_errors_raise_immediately():
    """Qwen: 401, 402, and invalid-model errors raise immediately with no retry."""
    from test_llm_providers import call_qwen_with_client

    for error_msg in ("401 Unauthorized", "402 Payment Required", "Model not found: invalid-model"):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception(error_msg)

        with pytest.raises(Exception) as exc_info:
            call_qwen_with_client(mock_client, "test-model", "Test prompt")

        assert error_msg in str(exc_info.value)
        assert mock_client.chat.completions.create.call_count == 1  # No retry!
