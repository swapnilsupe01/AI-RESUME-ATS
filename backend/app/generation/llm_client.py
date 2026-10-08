"""Provider-agnostic JSON LLM client: Groq -> Hugging Face -> local fallback."""
import json
import os
import re
import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HF_URL = "https://router.huggingface.co/v1/chat/completions"


class LLMUnavailable(Exception):
    """Raised when no remote provider worked; caller should use the local engine."""


def _providers():
    order = os.getenv("LLM_PROVIDER", "groq").lower()
    all_p = {
        "groq": (GROQ_URL, os.getenv("GROQ_API_KEY"),
                 os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")),
        "hf": (HF_URL, os.getenv("HF_TOKEN"),
               os.getenv("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")),
    }
    names = [order] + [n for n in all_p if n != order]
    return [(n, *all_p[n]) for n in names if n in all_p and all_p[n][1]]


def _parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


async def complete_json(system: str, user: str, timeout: float = 20.0) -> dict:
    """
    Send a chat completion request expecting a JSON response.
    Tries each configured provider (Groq first, then HF) with up to 2 attempts each.
    Raises LLMUnavailable if all providers fail.
    """
    last_err = None
    for name, url, key, model in _providers():
        for attempt in range(2):  # max 2 tries per provider
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    r = await client.post(
                        url,
                        headers={"Authorization": f"Bearer {key}"},
                        json={
                            "model": model,
                            "temperature": 0.3,
                            "response_format": {"type": "json_object"},
                            "messages": [
                                {"role": "system", "content": system},
                                {"role": "user", "content": user},
                            ],
                        },
                    )
                if r.status_code in (429, 500, 502, 503, 504):
                    last_err = f"{name}: HTTP {r.status_code}"
                    continue
                r.raise_for_status()
                return _parse_json(r.json()["choices"][0]["message"]["content"])
            except (httpx.TimeoutException, httpx.HTTPError, ValueError, KeyError) as e:
                last_err = f"{name}: {e}"
    raise LLMUnavailable(last_err or "no provider configured")
