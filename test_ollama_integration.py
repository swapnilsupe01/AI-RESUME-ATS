"""
End-to-End Ollama Gemma 3 12B Integration Test.

Tests:
  1. Ollama connectivity (GET /api/tags)
  2. Model detection (gemma3:12b installed)
  3. Raw Ollama generation via OllamaClient
  4. Validator pipeline (rewrite_with_validation) using Ollama
  5. Hallucination/preservation checks on LLM output
  6. Retry/correction mechanism
  7. Full resume transformation test with the specified test input
"""

import os
import sys
import json
from pathlib import Path

# Fix Windows console encoding for Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Setup paths and env ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = PROJECT_ROOT / "backend"
BACKEND_ENV = BACKEND_DIR / ".env"

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

# Load backend env
from dotenv import load_dotenv
load_dotenv(BACKEND_ENV, override=True)

# Force Ollama model for this test
os.environ["OLLAMA_MODEL"] = "gemma3:12b"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

# ── Test Results Tracker ──────────────────────────────────────────────────────
results = {
    "ollama_connection": "NOT_TESTED",
    "model_detected": "NOT_TESTED",
    "generation_test": "NOT_TESTED",
    "validator_result": "NOT_TESTED",
    "retry_result": "NOT_TESTED",
    "resume_transformation": "NOT_TESTED",
    "hallucination_check": "NOT_TESTED",
    "files_changed": [],
    "issues": [],
}


def header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ──────────────────────────────────────────────────────────────────────────────
# TEST 1: Ollama Connectivity
# ──────────────────────────────────────────────────────────────────────────────
header("TEST 1: Ollama Connectivity")
try:
    import httpx
    resp = httpx.get("http://localhost:11434/api/tags", timeout=5.0)
    if resp.status_code == 200:
        data = resp.json()
        models = data.get("models", [])
        model_names = [m["name"] for m in models]
        print(f"  ✅ Ollama is running. Models found: {model_names}")
        results["ollama_connection"] = "PASS"

        # TEST 2: gemma3:12b detection
        if any("gemma3:12b" in name for name in model_names):
            print(f"  ✅ gemma3:12b is installed")
            results["model_detected"] = "gemma3:12b"
        else:
            print(f"  ❌ gemma3:12b NOT found in: {model_names}")
            results["model_detected"] = f"MISSING (found: {model_names})"
            results["issues"].append("gemma3:12b not installed in Ollama")
    else:
        print(f"  ❌ Ollama returned status {resp.status_code}")
        results["ollama_connection"] = f"FAIL ({resp.status_code})"
except Exception as e:
    print(f"  ❌ Cannot connect to Ollama: {e}")
    results["ollama_connection"] = f"FAIL ({e})"
    results["issues"].append(f"Ollama connectivity failed: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# TEST 3: Raw Ollama Generation via OllamaClient
# ──────────────────────────────────────────────────────────────────────────────
header("TEST 3: OllamaClient Generation Test")

TEST_INPUT_1 = (
    "Computer Engineering student with hands-on experience in software development, "
    "ERP systems, cybersecurity, ISO 27001 compliance, AI/ML, and cloud deployment."
)

try:
    from app.generation.ollama_client import OllamaClient

    client = OllamaClient()
    print(f"  Ollama configured: {client.is_configured()}")
    print(f"  Model: {client.get_model_name()}")

    if client.is_configured():
        raw_result = client.generate(
            "rewrite_summary",
            TEST_INPUT_1,
            {
                "candidate_tools": ["Python", "FastAPI", "Docker", "ISO 27001", "AI/ML"],
                "jd_keywords": "cybersecurity, cloud, REST APIs",
                "rag_context": "",
            }
        )
        if raw_result:
            print(f"\n  Original:  {TEST_INPUT_1}")
            print(f"  Generated: {raw_result}")
            results["generation_test"] = "PASS"

            # Hallucination check
            hallucination_flags = []
            forbidden_claims = [
                "5+ years", "expert", "certified", "percentage",
                "10+ years", "proven track record of leading",
                "revenue", "cost savings",
            ]
            for claim in forbidden_claims:
                if claim.lower() in raw_result.lower():
                    hallucination_flags.append(claim)

            if hallucination_flags:
                print(f"\n  ⚠️  Hallucination detected: {hallucination_flags}")
                results["hallucination_check"] = f"WARNING ({hallucination_flags})"
            else:
                print(f"\n  ✅ No hallucination detected in generated output")
                results["hallucination_check"] = "PASS"
        else:
            print(f"  ❌ OllamaClient.generate() returned None")
            results["generation_test"] = "FAIL (returned None)"
    else:
        print(f"  ❌ OllamaClient not configured/available")
        results["generation_test"] = "FAIL (not configured)"

except Exception as e:
    print(f"  ❌ Generation test failed: {e}")
    results["generation_test"] = f"FAIL ({e})"
    import traceback; traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────────────
# TEST 4: Validator Pipeline with Ollama (rewrite_with_validation)
# ──────────────────────────────────────────────────────────────────────────────
header("TEST 4: Validator Pipeline (rewrite_with_validation)")

FULL_ORIGINAL = (
    "Computer Engineering student with hands-on experience in software development, "
    "ERP systems, cybersecurity, ISO 27001 compliance, AI/ML, and cloud deployment.\n\n"
    "Experienced in developing enterprise and business applications, REST APIs, "
    "security and compliance platforms, and vulnerability assessment solutions across "
    "requirements analysis, development, testing, and deployment.\n\n"
    "Strong interest in cybersecurity risk, security controls, technology consulting, "
    "and technology transformation."
)

KEYWORDS = [
    "Computer Engineering",
    "software development",
    "ERP systems",
    "cybersecurity",
    "cloud deployment",
    "enterprise",
    "REST APIs",
    "vulnerability assessment",
    "testing",
    "deployment",
    "security",
    "compliance",
]

try:
    from validator import rewrite_with_validation, validate

    def call_ollama_llm(prompt: str) -> str:
        """Callable wrapper for Ollama that works with rewrite_with_validation."""
        import httpx
        with httpx.Client(timeout=120.0) as http_client:
            resp = http_client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "gemma3:12b",
                    "messages": [
                        {"role": "system", "content": "You are a professional executive resume editor. "
                         "MANDATORY RULES: "
                         "1. Do NOT invent tools, technologies, numbers, or claims. "
                         "2. Each sentence: max 30 words and max 4 list separators. "
                         "3. Preserve ALL technical keywords from the original. "
                         "4. Return ONLY the rewritten text."},
                        {"role": "user", "content": prompt},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 512},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data.get("message", {}).get("content", "").strip()
                # Strip preambles
                import re
                text = re.sub(
                    r"^(?:(?:Sure,?\s*)?(?:Here(?:'s|\s+is)|This\s+is|Below\s+is))\s+[^:]+:\s*",
                    "", text, flags=re.IGNORECASE
                ).strip()
                if (text.startswith('"') and text.endswith('"')):
                    text = text[1:-1].strip()
                return text
            return ""

    result = rewrite_with_validation(
        call_ollama_llm,
        FULL_ORIGINAL,
        keywords=KEYWORDS,
        max_retries=2,
    )

    print(f"\n  [Status]:       {result['status']}")
    print(f"  [Retries Used]: {result['retries_used']}")
    print(f"\n  [Generated Summary]:")
    for line in result["summary"].split("\n"):
        print(f"    {line}")

    if result["issues"]:
        print(f"\n  [Remaining Issues]:")
        for issue in result["issues"]:
            print(f"    - {issue}")
    else:
        print(f"\n  ✅ No validation issues — passed all heuristic checks")

    results["validator_result"] = str(result["status"])
    results["retry_result"] = f"{result['retries_used']} retries used"

    # Additional hallucination verification on the final output
    forbidden_in_output = [
        "5+ years", "expert", "certified", "percentage improvements",
        "leading teams", "managed", "budget", "revenue",
    ]
    detected = [f for f in forbidden_in_output if f.lower() in result["summary"].lower()]
    if detected:
        print(f"\n  ⚠️  Potential hallucination in final output: {detected}")
        results["issues"].append(f"Hallucination in validated output: {detected}")
    else:
        print(f"\n  ✅ Final output passed hallucination spot-check")

except Exception as e:
    print(f"  ❌ Validator pipeline test failed: {e}")
    results["validator_result"] = f"FAIL ({e})"
    import traceback; traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────────────
# TEST 5: Resume Transformation via OllamaClient.generate (all 3 paragraphs)
# ──────────────────────────────────────────────────────────────────────────────
header("TEST 5: Full Resume Transformation (3 paragraphs)")

TEST_INPUTS = [
    "Computer Engineering student with hands-on experience in software development, "
    "ERP systems, cybersecurity, ISO 27001 compliance, AI/ML, and cloud deployment.",

    "Experienced in developing enterprise and business applications, REST APIs, "
    "security and compliance platforms, and vulnerability assessment solutions across "
    "requirements analysis, development, testing, and deployment.",

    "Strong interest in cybersecurity risk, security controls, technology consulting, "
    "and technology transformation.",
]

try:
    from app.generation.ollama_client import OllamaClient
    from app.generation.preservation_validator import validate_suggestion_output
    from app.generation.hallucination_guard import classify_suggestion

    client = OllamaClient()
    all_passed = True

    for i, original in enumerate(TEST_INPUTS, 1):
        print(f"\n  --- Paragraph {i} ---")
        print(f"  Original:  {original}")

        rewritten = client.generate(
            "rewrite_summary",
            original,
            {
                "candidate_tools": [
                    "Python", "FastAPI", "REST APIs", "ISO 27001",
                    "AI/ML", "Docker", "cybersecurity",
                ],
                "jd_keywords": "cybersecurity, cloud, software development, REST APIs",
                "rag_context": "",
            }
        )

        if rewritten:
            print(f"  Rewritten: {rewritten}")

            # Validate with preservation validator
            val_text, is_valid, val_reason = validate_suggestion_output(
                original, rewritten, "SUMMARY",
                ["Python", "FastAPI", "REST APIs", "ISO 27001", "AI/ML", "Docker", "cybersecurity"]
            )
            print(f"  Valid: {is_valid} | Reason: {val_reason[:80] if val_reason else 'N/A'}")

            # Hallucination guard
            status, note = classify_suggestion(
                original, rewritten,
                ["Python", "FastAPI", "REST APIs", "ISO 27001", "AI/ML", "Docker", "cybersecurity"]
            )
            print(f"  Evidence: {status} | {note[:80] if note else 'N/A'}")

            if not is_valid:
                all_passed = False
                print(f"  ⚠️  Validation failed — using fallback text")
        else:
            print(f"  ❌ No output generated")
            all_passed = False

    results["resume_transformation"] = "PASS" if all_passed else "PARTIAL (some validations failed)"

except Exception as e:
    print(f"  ❌ Resume transformation test failed: {e}")
    results["resume_transformation"] = f"FAIL ({e})"
    import traceback; traceback.print_exc()


# ──────────────────────────────────────────────────────────────────────────────
# FINAL REPORT
# ──────────────────────────────────────────────────────────────────────────────
header("FINAL REPORT")

results["files_changed"] = [
    "backend/app/ai/local_provider.py (added gemma3 to MODEL_PREFERENCE_ORDER, increased timeout)",
    "backend/app/generation/ollama_client.py (NEW — Ollama LLM client)",
    "backend/app/generation/resume_upgrade_engine.py (added Ollama fallback in all generation paths)",
    "backend/.env (OLLAMA_MODEL=gemma3:12b)",
    "test_ollama_integration.py (NEW — this end-to-end test)",
]

for key, val in results.items():
    if key == "files_changed":
        print(f"\n  📁 Files Changed:")
        for f in val:
            print(f"     • {f}")
    elif key == "issues":
        if val:
            print(f"\n  ⚠️  Remaining Issues:")
            for issue in val:
                print(f"     • {issue}")
        else:
            print(f"\n  ✅ No remaining issues")
    else:
        status_icon = "✅" if "PASS" in str(val) or "passed" in str(val).lower() else "⚠️" if "WARNING" in str(val) or "PARTIAL" in str(val) else "❌" if "FAIL" in str(val) else "ℹ️"
        print(f"  {status_icon} {key}: {val}")

print(f"\n{'=' * 60}")
print(f"  Test Complete")
print(f"{'=' * 60}\n")
