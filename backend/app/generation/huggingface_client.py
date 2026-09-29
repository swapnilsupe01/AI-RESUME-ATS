"""
Hugging Face Inference Client — Layer E AI Resume Upgrade Engine.

Primary model: meta-llama/Llama-3.2-3B-Instruct / Qwen/Qwen2.5-7B-Instruct.
Fallback models: Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.3, Phi-3.5-mini-instruct.

Uses huggingface_hub.InferenceClient with intelligent multi-provider and model fallbacks:
  1. Direct Hugging Face Serverless endpoint (requires zero 3rd-party provider config)
  2. HF Inference Providers (provider="auto" / "hf-inference")
  3. Seamless model fallback cascade if a specific model is offline or unserved.

Design decisions:
  - Token read from HF_TOKEN env var; never logged or returned to clients.
  - Model configurable via HF_MODEL env var; defaults to top serverless models.
  - Role-specific context (backend, DevOps, data/ML, cybersecurity, etc.) is
    injected into prompts from the JD.
  - Exponential backoff with jitter on OverloadedError / rate-limit (429).
  - Returns None on any failure so callers gracefully fall back to deterministic local upgrade.
  - Does NOT hallucinate: instructions explicitly forbid inventing data.
"""

import os
import re
import time
import random
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model configuration & Fallback Cascade
# ---------------------------------------------------------------------------
_DEFAULT_PRIMARY = "meta-llama/Llama-3.2-3B-Instruct"

_FALLBACK_CANDIDATES = [
    "Qwen/Qwen2.5-7B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "microsoft/Phi-3.5-mini-instruct",
    "HuggingFaceH4/zephyr-7b-beta",
]

# Retry configuration for OverloadedError / rate-limit
_MAX_RETRIES      = 3       # attempts per model
_BASE_BACKOFF_S   = 2.0     # base seconds for first retry
_MAX_BACKOFF_S    = 15.0    # cap exponential growth
_JITTER_FRACTION  = 0.3     # ±30% random jitter

# Role-specific context snippets injected into prompts.
_ROLE_CONTEXT: Dict[str, str] = {
    "backend":      "Target: backend/software engineering. Prioritise REST API design, "
                    "system scalability, microservices, SQL/NoSQL, and CI/CD mentions.",
    "devops":       "Target: DevOps/SRE. Prioritise cloud infrastructure, container "
                    "orchestration (Kubernetes/Docker), IaC, monitoring, and SLO/SLA metrics.",
    "data":         "Target: data/ML engineering. Prioritise ML model development, "
                    "data pipelines, feature engineering, model evaluation metrics, and "
                    "frameworks such as PyTorch, TensorFlow, scikit-learn, and Spark.",
    "cybersecurity":"Target: cybersecurity/information security. Prioritise vulnerability "
                    "assessment, SIEM, penetration testing, compliance (SOC2/ISO27001), "
                    "and incident response experience.",
    "frontend":     "Target: frontend/UI engineering. Prioritise React/Vue/Angular, "
                    "accessibility, performance optimisation, and design-system work.",
    "fullstack":    "Target: full-stack engineering. Balance frontend (React) and backend "
                    "(FastAPI/Node) skills, and mention database and deployment work.",
}

_SYSTEM_MSG = (
    "You are a professional executive resume editor. "
    "Your goal is to elevate resume phrasing into clear, professional, impactful engineering language. "
    "MANDATORY ANTI-HALLUCINATION RULES:\n"
    "1. NEVER invent or inject tools, technologies, frameworks, cloud services (e.g., AWS, Ansible, Docker, Kubernetes, Jenkins), "
    "companies, metrics, or degrees not explicitly mentioned in the candidate's original text or candidate skills.\n"
    "2. If the candidate does not mention a technology, DO NOT add it. Only refine the wording, action verbs, and structure.\n"
    "3. Use strong action verbs (Architected, Engineered, Developed, Designed, Automated, Streamlined, Implemented).\n"
    "4. Return ONLY the improved text directly without any conversational preamble or labels."
)

_USER_TEMPLATES: Dict[str, str] = {
    "rewrite_summary": (
        "Rewrite this professional summary to be concise, impactful, and clearly worded. "
        "Preserve all facts. Do NOT invent new skills, certifications, or tools.\n\n"
        "ORIGINAL SUMMARY:\n{original}\n\n"
        "CANDIDATE SKILLS (only use tools from this list or the original text):\n{candidate_tools}\n\n"
        "Return ONLY the rewritten summary:"
    ),
    "rewrite_experience": (
        "Rewrite this work experience bullet to start with a strong action verb, "
        "highlight technical clarity, and sound highly professional. "
        "STRICT RULE: Do NOT invent or add any tools, technologies, or numbers not present in the original bullet.\n\n"
        "ORIGINAL BULLET:\n{original}\n\n"
        "CANDIDATE TOOLS (reference only if relevant to this bullet):\n{candidate_tools}\n\n"
        "Return ONLY the improved bullet:"
    ),
    "rewrite_project": (
        "Refine this project description into a clear, concise, and professional engineering summary (1-2 sentences). "
        "Focus on the functional scope, core capability, architecture, and real-world problem solved. "
        "CRITICAL RULES:\n"
        "1. Do NOT awkwardly cram or list every programming language and tool into a run-on sentence. Focus on what the system does.\n"
        "2. Do NOT invent unmentioned technologies or claims.\n"
        "3. Provide ONLY one single, direct polished description — do NOT provide alternative options or conversational preamble.\n\n"
        "ORIGINAL SUMMARY / TAGLINE:\n{original}\n\n"
        "Return ONLY the single improved description:"
    ),
    "tailor_to_jd": (
        "Polish this resume text to sound highly professional. "
        "Only rephrase using the candidate's existing experience and skills. "
        "STRICT RULE: Do NOT add new tools or achievements.\n\n"
        "ORIGINAL TEXT:\n{original}\n\n"
        "Return ONLY the improved text:"
    ),
    "improve_achievement": (
        "Improve this bullet to clearly communicate engineering quality and impact with professional wording. "
        "Do NOT invent numbers or unmentioned technologies.\n\n"
        "ORIGINAL ACHIEVEMENT:\n{original}\n\n"
        "Return ONLY the improved achievement:"
    ),
}


class HuggingFaceClient:
    """
    Hugging Face Inference API client with intelligent provider & model fallbacks.
    Returns None on any error so the caller can fall back to local generation.
    """

    def __init__(self):
        self._token: Optional[str] = os.getenv("HF_TOKEN", "").strip() or None
        configured_model = os.getenv("HF_MODEL", "").strip()
        self._model: str = configured_model if configured_model else _DEFAULT_PRIMARY
        self._timeout: float = float(os.getenv("HF_TIMEOUT", "45.0"))
        self._available: Optional[bool] = None  # cached after first check
        self._active_model: str = self._model
        self._clients: List[Any] = []  # list of initialized InferenceClient variants

    # ── Public API ────────────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Return True if HF_TOKEN is set in the environment."""
        return self._token is not None

    def is_available(self) -> bool:
        """
        Check whether the model endpoint is reachable.
        Result is cached until process restart to avoid repeated round-trips.
        """
        if self._available is not None:
            return self._available
        if not self._token:
            self._available = False
            return False
        try:
            # Check availability with quick probe
            res = self._call_api("Hello")
            self._available = res is not None
        except Exception as exc:
            logger.warning("[HF] Availability check failed: %s (%s)", type(exc).__name__, exc)
            self._available = False
        return self._available

    def generate(
        self,
        task_type: str,
        original: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Call the HF model for the given task type.

        Args:
            task_type: One of 'rewrite_summary', 'rewrite_experience',
                       'rewrite_project', 'tailor_to_jd', 'improve_achievement'.
            original:  The original text to improve.
            context:   Task-specific context values merged into the prompt template.
                       May include 'target_role' key to inject role-specific guidance.

        Returns:
            Cleaned generated text string, or None on failure.
        """
        if not self.is_configured():
            logger.debug("[HF] Token not configured — skipping HF call.")
            return None

        if task_type not in _USER_TEMPLATES:
            logger.warning("[HF] Unknown task_type: %s", task_type)
            return None

        ctx = context or {}
        role_key = str(ctx.get("target_role", "")).lower().strip()
        role_ctx = ""
        for k, snippet in _ROLE_CONTEXT.items():
            if k in role_key:
                role_ctx = snippet + "\n\n"
                break

        user_msg = self._build_user_message(task_type, original, ctx, role_ctx)
        raw = self._call_api(user_msg)
        if raw is None:
            return None

        return self._clean_output(raw, original)

    def get_model_name(self) -> str:
        return self._active_model

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_clients(self) -> List[Any]:
        """Lazy-initialise and return available InferenceClient configurations."""
        if not self._clients:
            try:
                from huggingface_hub import InferenceClient

                # Strategy 1: Direct native InferenceClient (works without enabling third-party providers)
                try:
                    c_direct = InferenceClient(token=self._token, timeout=self._timeout)
                    self._clients.append(c_direct)
                except Exception as e:
                    logger.debug("[HF] Direct client init exception: %s", e)

                # Strategy 2: hf-inference serverless provider
                try:
                    c_hf = InferenceClient(provider="hf-inference", token=self._token, timeout=self._timeout)
                    self._clients.append(c_hf)
                except Exception as e:
                    logger.debug("[HF] hf-inference client init exception: %s", e)

                # Strategy 3: Auto provider (used when 3rd-party providers are enabled in user HF account)
                try:
                    c_auto = InferenceClient(provider="auto", api_key=self._token, token=self._token, timeout=self._timeout)
                    self._clients.append(c_auto)
                except Exception as e:
                    logger.debug("[HF] Auto provider client init exception: %s", e)

            except ImportError:
                logger.error(
                    "[HF] huggingface_hub is not installed. "
                    "Run: pip install huggingface-hub>=0.20.0"
                )
                raise
        return self._clients

    def _build_user_message(
        self,
        task_type: str,
        original: str,
        context: Dict[str, Any],
        role_ctx: str,
    ) -> str:
        """Merge context into the user message template."""
        template = _USER_TEMPLATES[task_type]
        defaults = {
            "original":        original,
            "jd_keywords":     context.get("jd_keywords", ""),
            "candidate_tools": ", ".join(context.get("candidate_tools", [])),
            "technologies":    ", ".join(context.get("technologies", [])),
            "jd_snippet":      context.get("jd_snippet", ""),
            "role_context":    role_ctx,
            "rag_context":     context.get("rag_context", ""),
        }
        try:
            return template.format(**defaults)
        except KeyError as exc:
            logger.warning("[HF] Prompt template key error: %s", exc)
            return original

    def _call_api(self, user_message: str) -> Optional[str]:
        """
        Call HF Inference API with multi-model and multi-client fallback cascade.
        """
        try:
            clients = self._get_clients()
        except Exception:
            return None

        if not clients:
            return None

        messages = [
            {"role": "system", "content": _SYSTEM_MSG},
            {"role": "user",   "content": user_message},
        ]

        # Build prioritized models list
        models_to_try: List[str] = [self._active_model]
        for m in [_DEFAULT_PRIMARY] + _FALLBACK_CANDIDATES:
            if m not in models_to_try:
                models_to_try.append(m)

        for model in models_to_try:
            for client in clients:
                result = self._try_model(client, model, messages)
                if result is not None:
                    if model != self._active_model:
                        logger.info("[HF] Active model selected: %s", model)
                        self._active_model = model
                    return result

        logger.warning("[HF] All fallback models and providers exhausted.")
        return None

    def _try_model(self, client: Any, model: str, messages: list) -> Optional[str]:
        """
        Attempt calls to one model/client combination with exponential backoff on transient errors.
        Immediately returns None on 400/404/422/unsupported model errors so fallback can trigger quickly.
        """
        try:
            from huggingface_hub.errors import (
                OverloadedError,
                BadRequestError,
                HfHubHTTPError,
            )
        except ImportError:
            try:
                from huggingface_hub import (  # type: ignore
                    OverloadedError,
                    BadRequestError,
                    HfHubHTTPError,
                )
            except ImportError:
                OverloadedError  = Exception
                BadRequestError  = Exception
                HfHubHTTPError   = Exception

        for attempt in range(_MAX_RETRIES):
            try:
                if hasattr(client, "chat") and hasattr(client.chat, "completions"):
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=400,
                        temperature=0.25,
                    )
                elif hasattr(client, "chat_completion"):
                    response = client.chat_completion(
                        messages=messages,
                        model=model,
                        max_tokens=400,
                        temperature=0.25,
                    )
                else:
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=400,
                        temperature=0.25,
                    )

                text = response.choices[0].message.content or ""
                return text.strip() if text.strip() else None

            except OverloadedError as exc:
                wait = self._backoff(attempt)
                logger.warning(
                    "[HF] Model %s overloaded (attempt %d/%d). Retrying in %.1fs. (%s)",
                    model, attempt + 1, _MAX_RETRIES, wait, exc,
                )
                time.sleep(wait)

            except Exception as exc:
                err_str = str(exc)
                status = self._extract_status_code(err_str)

                if status == 401 or "unauthorized" in err_str.lower() or "invalid token" in err_str.lower():
                    logger.error("[HF] Invalid token (401). Check HF_TOKEN.")
                    self._available = False
                    return None  # fatal auth error

                # Non-retryable errors for this endpoint/model (model not supported, 404, bad request)
                if (
                    status in (400, 404, 422)
                    or "not supported" in err_str.lower()
                    or "model_not_supported" in err_str.lower()
                    or "does not support" in err_str.lower()
                ):
                    logger.debug(
                        "[HF] Model %s not supported on current client/provider (%s). Trying fallback.",
                        model, status or "not supported",
                    )
                    return None  # immediately break and try next strategy/model

                if status == 429:
                    wait = self._backoff(attempt)
                    logger.warning(
                        "[HF] Rate limited (429, attempt %d/%d). Retrying in %.1fs.",
                        attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)

                elif status == 503 or "loading" in err_str.lower():
                    wait = min(self._backoff(attempt) * 2, _MAX_BACKOFF_S)
                    logger.info(
                        "[HF] Model %s loading (503, attempt %d/%d). Waiting %.1fs.",
                        model, attempt + 1, _MAX_RETRIES, wait,
                    )
                    time.sleep(wait)

                else:
                    logger.warning(
                        "[HF] Request failed (attempt %d/%d, model %s): %s (%s)",
                        attempt + 1, _MAX_RETRIES, model, type(exc).__name__, exc,
                    )
                    if attempt < _MAX_RETRIES - 1:
                        time.sleep(self._backoff(attempt))

        return None

    @staticmethod
    def _backoff(attempt: int) -> float:
        """Exponential backoff with ±30% jitter."""
        raw = min(_BASE_BACKOFF_S * (2 ** attempt), _MAX_BACKOFF_S)
        return raw * (1.0 + _JITTER_FRACTION * (2 * random.random() - 1))

    @staticmethod
    def _extract_status_code(err_str: str) -> Optional[int]:
        """Try to extract an HTTP status code from an exception string."""
        m = re.search(r"\b(4\d\d|5\d\d)\b", err_str)
        return int(m.group(1)) if m else None

    def _clean_output(self, raw: str, original: str) -> Optional[str]:
        """
        Post-process the model output.
        - Strip common artefacts (preambles, labels, tags, redundant markdown headers, leading quotes).
        - Validate minimum quality gate.
        """
        if not raw:
            return None

        text = raw
        text = re.sub(r"\[/?INST\]", "", text).strip()

        # Remove conversational preambles like "Here is the rewritten project description: ...", "Sure, here's ...:", "A rewritten project description: ..."
        text = re.sub(
            r"^(?:(?:Sure,?\s*)?(?:Here(?:'s|\s+is)|This\s+is|Below\s+is|A|An|The)\s+)?(?:the\s+)?(?:rewritten|improved|suggested|updated|an|new)?\s*(?:project\s+description|project\s+summary|project|bullet\s+point|bullet|summary|description|text|achievement|resume\s+bullet)?\s*:+\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        # Handle standalone "Here is ..." leading sentences
        text = re.sub(
            r"^(?:Sure,?\s*)?(?:Here(?:'s|\s+is)|Below\s+is)\s+[^:]+:\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        # Strip leading labels
        text = re.sub(
            r"^(?:IMPROVED|REWRITTEN|SUGGESTED|UPDATED)\s+(?:BULLET(?:\s+POINT)?|DESCRIPTION|PROJECT\s+DESCRIPTION|PROJECT|TEXT|SUMMARY|ACHIEVEMENT)\s*:+\s*",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        # Remove markdown heading noise if model returned labeled sections
        text = re.sub(r"\*\*(?:Key Contributions|Outcome|Key Highlights|Deliverables)\s*:?\*\*", "", text)

        # Strip secondary options or alternative suggestions (e.g. "Or, alternatively: ...", "Alternative: ...")
        alt_match = re.search(r"\b(?:Or,?\s+alternatively|Alternatively|Alternative\s*\d*|Option\s*2)\s*:\s*", text, flags=re.IGNORECASE)
        if alt_match:
            text = text[:alt_match.start()].strip()

        # Remove surrounding quotes if the entire output is quoted
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        # Minimal quality gate
        if len(text) < 15:
            logger.warning("[HF] Output too short (%d chars), discarding.", len(text))
            return None

        if text.strip().lower() == original.strip().lower():
            logger.debug("[HF] Output identical to original, discarding.")
            return None

        return text.strip()


# Module-level singleton — loaded once per process
hf_client = HuggingFaceClient()
