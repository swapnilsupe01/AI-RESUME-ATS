import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Locate .env relative to this script and project root.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR

for env_path in (
    PROJECT_ROOT / ".env",
    PROJECT_ROOT / "backend" / ".env",
    PROJECT_ROOT.parent / "backend" / ".env",
):
    if env_path.is_file():
        load_dotenv(env_path, override=False)

load_dotenv(override=False)

# Ensure validator can be imported
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT.parent))

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
    """Call Groq using OpenAI-compatible client or Hugging Face InferenceClient."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key,
            timeout=60.0,
            max_retries=0,
        )
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": "You are a careful resume editor."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""

    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("Neither GROQ_API_KEY nor HF_TOKEN is configured. Add credentials to your .env file.")

    client = InferenceClient(api_key=token, timeout=60)
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b:groq"),
        messages=[
            {"role": "system", "content": "You are a careful resume editor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def call_qwen_with_client(client, model: str, prompt: str) -> str:
    """
    Executes a Qwen call with 60s timeout and exactly 1 retry on ReadTimeout.
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


def call_qwen(prompt: str) -> str:
    """Call Qwen through Hugging Face/DeepInfra routing."""
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN is missing. Add it to your .env file.")

    client = InferenceClient(api_key=token, timeout=60)
    model = os.getenv("QWEN_MODEL", "Qwen/Qwen3.8-27B:deepinfra")
    return call_qwen_with_client(client, model, prompt)


def call_deepseek(prompt: str) -> str:
    """Call DeepSeek through Hugging Face/DeepInfra routing."""
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN is missing. Add it to your .env file.")

    client = InferenceClient(api_key=token, timeout=60)
    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V4.1-Flash:deepinfra"),
        messages=[
            {"role": "system", "content": "You are a careful resume editor."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


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
    providers = {
        "Groq": call_groq,
        "Qwen via DeepInfra": call_qwen,
        "DeepSeek via DeepInfra": call_deepseek,
    }

    for name, call_fn in providers.items():
        run_provider(name, call_fn)
