import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ── Canonical env source: backend/.env only ───────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR
BACKEND_ENV = PROJECT_ROOT / "backend" / ".env"

if not BACKEND_ENV.is_file():
    raise FileNotFoundError(f"backend/.env not found at {BACKEND_ENV}. Create it before running this script.")

load_dotenv(BACKEND_ENV, override=True)  # override=True so backend/.env always wins

# Ensure validator can be imported
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from openai import OpenAI
from huggingface_hub import InferenceClient
from validator import rewrite_with_validation

ORIGINAL_SUMMARY = """
Highly motivated Computer Engineering student with hands-on experience
in software development, ERP systems, cybersecurity, and cloud deployment.
Proven expertise in developing enterprise and business applications,
REST APIs, security and compliance platforms, and vulnerability assessment
solutions through requirements analysis, development, testing, and deployment.
Strong interest in cybersecurity risk, security controls, technology consulting,
and technology transformation.
""".strip()

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
]


def call_groq(prompt: str) -> str:
    """Call Groq via its OpenAI-compatible API. Requires GROQ_API_KEY."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not set in backend/.env — skipping Groq.")

    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=groq_api_key,
        timeout=60.0,
        max_retries=0,
    )
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama3-8b-8192"),
        messages=[
            {"role": "system", "content": "You are a careful resume editor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def call_qwen_with_client(client, model: str, prompt: str) -> str:
    """
    Executes a chat call with 60s timeout and exactly 1 retry on ReadTimeout.
    Raises 401, 402, and invalid-model errors immediately with no retry.
    """
    max_attempts = 2  # 1 initial + 1 retry on ReadTimeout
    for attempt in range(max_attempts):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a careful resume editor."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            exc_str = str(exc).lower()
            status_code = getattr(exc, "status_code", None) or getattr(getattr(exc, "response", None), "status_code", None)

            # Non-retryable errors: 401, 402, invalid model
            if (
                status_code in (401, 402)
                or "401" in exc_str
                or "402" in exc_str
                or "unauthorized" in exc_str
                or "payment required" in exc_str
                or "invalid model" in exc_str
                or "model_not_found" in exc_str
                or "not found" in exc_str
            ):
                raise exc

            # ReadTimeout / timeout check: retry exactly once
            is_timeout = (
                isinstance(exc, TimeoutError)
                or "timeout" in exc_str
                or "timed out" in exc_str
                or "readtimeout" in type(exc).__name__.lower()
            )
            if is_timeout and attempt < max_attempts - 1:
                continue

            raise exc


# ── Free HF Serverless models (no :deepinfra, no credits needed) ─────────────
# Only chat-completion capable models that work on the free HF Serverless tier.
_HF_FREE_MODELS = [
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "HuggingFaceH4/zephyr-7b-beta",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
    "microsoft/Phi-3.5-mini-instruct",
]


def call_hf_serverless(prompt: str) -> str:
    """
    Call HF Serverless Inference (free tier, no credits needed).
    Tries a cascade of models until one responds successfully.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN is missing. Add it to backend/.env.")

    client = InferenceClient(api_key=token, timeout=60)
    preferred = os.getenv("HF_MODEL", "").strip()
    models = ([preferred] if preferred else []) + _HF_FREE_MODELS

    last_exc = None
    for model in models:
        try:
            return call_qwen_with_client(client, model, prompt)
        except Exception as exc:
            exc_str = str(exc).lower()
            status_code = getattr(exc, "status_code", None)
            # 402 means credits depleted for this model — skip to next
            if status_code == 402 or "402" in exc_str or "payment required" in exc_str:
                print(f"  [SKIP] {model} — credits depleted (402), trying next model.")
                last_exc = exc
                continue
            # 404 / not supported / not a chat model — skip to next
            if (
                status_code in (400, 404)
                or "not found" in exc_str
                or "not supported" in exc_str
                or "not a chat model" in exc_str
                or "model_not_supported" in exc_str
            ):
                print(f"  [SKIP] {model} — not available ({status_code or 'unsupported'}), trying next model.")
                last_exc = exc
                continue
            raise exc

    raise RuntimeError(f"All HF serverless models exhausted. Last error: {last_exc}")


def run_provider(name: str, call_fn):
    print(f"\n{'=' * 20} {name} {'=' * 20}")
    try:
        result = rewrite_with_validation(
            call_fn,
            ORIGINAL_SUMMARY,
            keywords=KEYWORDS,
            max_retries=2
        )
        print("\n[Final Summary]:")
        print(result["summary"])
        print(f"\n[Retries Used]: {result['retries_used']}")
        print(f"[Status]: {result['status']}")
        if result["issues"]:
            print("[Validation Issues]:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        else:
            print("[Validation Issues]: None (Passed all heuristic checks)")
    except Exception as exc:
        print(f"Request failed: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    has_groq = bool(os.getenv("GROQ_API_KEY"))
    has_hf   = bool(os.getenv("HF_TOKEN"))

    providers = {}
    if has_groq:
        providers["Groq"] = call_groq
    else:
        print("[INFO] GROQ_API_KEY not set — skipping Groq provider.")

    if has_hf:
        providers["HF Serverless (free)"] = call_hf_serverless
    else:
        print("[INFO] HF_TOKEN not set — skipping HF Serverless provider.")

    if not providers:
        print("[ERROR] No providers configured. Add HF_TOKEN to backend/.env.")
    else:
        for name, call_fn in providers.items():
            run_provider(name, call_fn)

