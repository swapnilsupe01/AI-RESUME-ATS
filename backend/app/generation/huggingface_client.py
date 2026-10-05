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

from app.generation.preservation_validator import (
    sanitize_ai_text,
    contains_ai_leakage,
)

logger = logging.getLogger(__name__)

# ── Multi-Provider & Model Configurations ────────────────────────────────────
_GROQ_DEFAULT_MODEL     = "openai/gpt-oss-120b"
_QWEN_DEFAULT_MODEL     = "Qwen/Qwen3.8-27B:deepinfra"
_DEEPSEEK_DEFAULT_MODEL = "deepseek-ai/DeepSeek-V4.1-Flash:deepinfra"
_DEFAULT_PRIMARY        = "meta-llama/Llama-3.2-3B-Instruct"

_FALLBACK_CANDIDATES = [
    _QWEN_DEFAULT_MODEL,
    _DEEPSEEK_DEFAULT_MODEL,
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
    "MANDATORY ANTI-HALLUCINATION, GRAMMAR & PRESERVATION RULES:\n"
    "1. MINIMAL, MEANING-PRESERVING EDITS: If the original sentence is already grammatically correct, "
    "clear, and impactful, retain it verbatim or make only minimal refinements. Do NOT rewrite sentences "
    "merely to swap synonymous verbs or change phrasing arbitrarily.\n"
    "2. CONTENT-TYPE PRESERVATION: A technology stack or skill list must ALWAYS remain a technology list. "
    "NEVER convert a list of technologies (e.g. 'React, FastAPI, Python, Docker') into a sentence or project description "
    "(e.g., NEVER generate 'Developed an application using...').\n"
    "3. NEVER invent or inject tools, technologies, frameworks, cloud services (e.g., AWS, Ansible, Docker, Kubernetes, Jenkins), "
    "companies, metrics, deployment claims, or degrees not explicitly mentioned in the candidate's original text or candidate skills.\n"
    "4. COMMA & PUNCTUATION PRECISION:\n"
    "   - Do NOT insert a comma before 'and' or 'or' in a compound predicate (two verbs sharing the same subject, "
    "e.g. write 'Implemented X using Docker and deployed Y', NEVER 'Implemented X using Docker, and deployed Y').\n"
    "   - ALWAYS PRESERVE the Oxford comma in lists of 3 or more items (e.g. 'analytics, reporting, and monitoring'; "
    "'feature A, feature B, and feature C'). Do not remove valid list commas.\n"
    "   - Ensure correct parallel structure across coordinated verbs, infinitives, and clauses.\n"
    "5. A project title must remain a concise title. An achievement must preserve all original numbers/percentages.\n"
    "6. NEVER rewrite or alter internship descriptions, certification names, or credential details. "
    "Those sections must be reproduced exactly as the student wrote them.\n"
    "7. Return ONLY the improved text directly without any conversational preamble or commentary."
)

_USER_TEMPLATES: Dict[str, str] = {
    "rewrite_summary": (
        "STEP 1 — READ AND MEMORIZE THE ORIGINAL SUMMARY BELOW. Every fact, tool, and number "
        "in the original must remain present in your output.\n\n"
        "ORIGINAL SUMMARY (memorize this — do NOT change any facts, tools, or numbers):\n{original}\n\n"
        "STEP 2 — Now rewrite it to be more concise, impactful, and clearly worded using strong "
        "action verbs. If already strong, retain it. Preserve ALL facts. Do NOT invent new skills, certifications, or tools.\n\n"
        "CANDIDATE SKILLS (only reference tools already in the original or this list):\n{candidate_tools}\n\n"
        "Return ONLY the rewritten summary:"
    ),
    "rewrite_experience": (
        "STEP 1 — READ AND MEMORIZE THE ORIGINAL BULLET BELOW. Every tool, technology, and "
        "fact in the original must remain present in your output. Do NOT invent anything new.\n\n"
        "ORIGINAL BULLET (memorize this verbatim):\n{original}\n\n"
        "STEP 2 — Evaluate the bullet. If it is already grammatically correct, strong, and clear, "
        "retain it verbatim or apply only minimal polish. Otherwise, refine it into professional engineering phrasing.\n"
        "CRITICAL RULES:\n"
        "1. STRICT PROHIBITION: Do NOT invent or add any tools, technologies, numbers, or deployment claims not in original.\n"
        "2. If the input is only a list of technologies, return ONLY the formatted technology list — NEVER convert it into a sentence.\n"
        "3. Provide EXACTLY ONE single bullet sentence for this item. Do NOT append descriptions of other projects or extra sections.\n"
        "4. Output MUST be ONLY the single rewritten bullet string without any commentary.\n"
        "5. PUNCTUATION & COMMAS: Use commas ONLY when required by sentence structure. "
        "Do NOT insert a comma before 'and' when joining two coordinated verbs sharing the subject "
        "(e.g., write 'Implemented isolated FastAPI sandbox execution using Docker and deployed the full-stack application', "
        "NOT '...using Docker, and deployed...'). "
        "ALWAYS preserve the Oxford comma in 3+ item lists (e.g., 'dashboards for analytics, reporting, and monitoring').\n"
        "6. PARALLEL STRUCTURE: Maintain grammatically parallel phrasing across coordinated clauses and infinitives "
        "(e.g., 'to identify matched skills and provide recommendations', not 'to identify ... and provided ...').\n\n"
        "CANDIDATE TOOLS (reference only if already present in the original bullet):\n{candidate_tools}\n\n"
        "Return ONLY the improved bullet:"
    ),
    "rewrite_project": (
        "STEP 1 — READ AND MEMORIZE THE ORIGINAL PROJECT DESCRIPTION BELOW. Every tool, "
        "technology, and functional claim in the original must remain present in your output. "
        "Do NOT invent any tools, frameworks, or enterprise claims.\n\n"
        "ORIGINAL PROJECT DESCRIPTION (memorize this verbatim):\n{original}\n\n"
        "STEP 2 — Refine it into a clear, concise, and professional engineering summary (1-2 sentences). "
        "If already clear and correct, retain it with minimal edits. "
        "Focus on the functional scope, core capability, architecture, and real-world problem solved.\n"
        "CRITICAL RULES:\n"
        "1. If the input is a list of technologies or tech stack (e.g. 'React, FastAPI, Python, Docker'), "
        "return ONLY the formatted list of technologies. NEVER invent project details or sentences like 'Developed a web application using...'.\n"
        "2. PUNCTUATION & COMMAS: Do NOT insert a comma before 'and' in two-verb compound predicates. "
        "PRESERVE Oxford commas in 3+ item lists.\n"
        "3. STRICT PROHIBITION: Do NOT invent unmentioned technologies, companies, or enterprise claims.\n"
        "4. Provide ONLY one single, direct polished description — do NOT provide alternative options.\n\n"
        "Return ONLY the single improved description:"
    ),
    "format_tech_stack": (
        "STEP 1 — Read the technology stack below:\n{original}\n\n"
        "STEP 2 — Return the exact same technology stack with clean, standardized comma-separated formatting. "
        "CRITICAL RULES: Do NOT invent any project descriptions, action verbs, sentences, or explanations.\n\n"
        "Return ONLY the clean technology stack:"
    ),
    "tailor_to_jd": (
        "STEP 1 — READ AND MEMORIZE THE ORIGINAL TEXT BELOW.\n\n"
        "ORIGINAL TEXT (memorize this verbatim):\n{original}\n\n"
        "STEP 2 — Polish the text to sound highly professional using only the candidate's existing "
        "experience and skills. STRICT RULE: Do NOT add new tools or achievements.\n\n"
        "Return ONLY the improved text:"
    ),
    "improve_achievement": (
        "STEP 1 — READ AND MEMORIZE THE ORIGINAL ACHIEVEMENT BELOW.\n\n"
        "ORIGINAL ACHIEVEMENT (memorize this verbatim):\n{original}\n\n"
        "STEP 2 — Improve the bullet to clearly communicate engineering quality and impact with "
        "professional wording. Do NOT invent numbers, percentages, or unmentioned technologies.\n\n"
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
        self._groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY", "").strip() or None
        self._groq_model: str = os.getenv("GROQ_MODEL", _GROQ_DEFAULT_MODEL).strip()
        self._qwen_model: str = os.getenv("QWEN_MODEL", _QWEN_DEFAULT_MODEL).strip()
        self._deepseek_model: str = os.getenv("DEEPSEEK_MODEL", _DEEPSEEK_DEFAULT_MODEL).strip()

        configured_model = os.getenv("HF_MODEL", "").strip()
        self._model: str = configured_model if configured_model else self._qwen_model
        self._timeout: float = float(os.getenv("HF_TIMEOUT", "60.0"))
        self._available: Optional[bool] = None  # cached after first check
        self._active_model: str = self._groq_model if self._groq_api_key else self._model
        self._clients: List[Any] = []  # list of initialized InferenceClient variants
        self._groq_client: Optional[Any] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Return True if HF_TOKEN or GROQ_API_KEY is set in the environment."""
        return bool(self._token or self._groq_api_key)

    def is_available(self) -> bool:
        """
        Check whether any configured model endpoint is reachable.
        Result is cached until process restart to avoid repeated round-trips.
        """
        if self._available is not None:
            return self._available
        if not self.is_configured():
            self._available = False
            return False
        try:
            # Check availability with quick probe
            res = self._call_api("Hello")
            self._available = res is not None
        except Exception as exc:
            logger.warning("[LLM] Availability check failed: %s (%s)", type(exc).__name__, exc)
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

        # Extract cross-project contamination guard list (private key, not sent to LLM)
        other_proj_names = ctx.get("_other_project_names") or None

        # Clean context for template formatting (strip internal/private keys)
        fmt_ctx = {k: v for k, v in ctx.items() if not k.startswith("_")}
        template = _USER_TEMPLATES[task_type]
        user_msg = role_ctx + template.format(original=original, **fmt_ctx)
        raw = self._call_api(user_msg)
        if raw is None:
            return None

        return self._clean_output(
            raw, original, task_type=task_type, other_project_names=other_proj_names
        )

    def get_model_name(self) -> str:
        return self._active_model

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_groq_client(self) -> Optional[Any]:
        """Lazy-initialize OpenAI-compatible Groq API client."""
        if not self._groq_api_key:
            return None
        if self._groq_client is None:
            try:
                from openai import OpenAI
                self._groq_client = OpenAI(
                    base_url="https://api.groq.com/openai/v1",
                    api_key=self._groq_api_key,
                    timeout=self._timeout,
                    max_retries=0,
                )
            except Exception as e:
                logger.warning("[LLM] Failed to initialize Groq OpenAI client: %s", e)
                return None
        return self._groq_client

    def _get_clients(self) -> List[Any]:
        """Lazy-initialise and return available InferenceClient configurations."""
        if not self._clients and self._token:
            try:
                from huggingface_hub import InferenceClient

                # Strategy 1: Direct native InferenceClient using api_key / token
                try:
                    c_direct = InferenceClient(api_key=self._token, timeout=self._timeout)
                    self._clients.append(c_direct)
                except TypeError:
                    try:
                        c_direct = InferenceClient(token=self._token, timeout=self._timeout)
                        self._clients.append(c_direct)
                    except Exception as e:
                        logger.debug("[HF] Direct token client init exception: %s", e)
                except Exception as e:
                    logger.debug("[HF] Direct api_key client init exception: %s", e)

                # Strategy 2: hf-inference serverless provider
                try:
                    c_hf = InferenceClient(provider="hf-inference", token=self._token, timeout=self._timeout)
                    self._clients.append(c_hf)
                except Exception as e:
                    logger.debug("[HF] hf-inference client init exception: %s", e)

                # Strategy 3: Auto provider (used when 3rd-party providers like DeepInfra are enabled)
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
        Call LLM Inference API with multi-provider and multi-model fallback cascade.
        Order:
          1. Groq (if GROQ_API_KEY is configured) -> model: GROQ_MODEL (e.g. openai/gpt-oss-120b)
          2. Qwen via DeepInfra on Hugging Face   -> model: QWEN_MODEL (e.g. Qwen/Qwen3.8-27B:deepinfra)
          3. DeepSeek via DeepInfra on Hugging Face -> model: DEEPSEEK_MODEL (e.g. deepseek-ai/DeepSeek-V4.1-Flash:deepinfra)
          4. Hugging Face Serverless fallback cascade
        """
        messages = [
            {"role": "system", "content": _SYSTEM_MSG},
            {"role": "user",   "content": user_message},
        ]

        # 1. Try Groq if configured
        groq_client = self._get_groq_client()
        if groq_client:
            try:
                resp = groq_client.chat.completions.create(
                    model=self._groq_model,
                    messages=messages,
                    temperature=0.2,
                )
                text = resp.choices[0].message.content or ""
                if text.strip():
                    self._active_model = f"groq:{self._groq_model}"
                    return text.strip()
            except Exception as e:
                logger.warning("[LLM] Groq request failed (%s): %s. Falling back to DeepInfra/HF.", type(e).__name__, e)

        # 2. Try Hugging Face / DeepInfra clients
        try:
            clients = self._get_clients()
        except Exception:
            clients = []

        if not clients:
            if not groq_client:
                logger.warning("[LLM] Neither GROQ_API_KEY nor HF_TOKEN is configured.")
            return None

        # Build prioritized models list: Qwen -> DeepSeek -> active -> fallbacks
        models_to_try: List[str] = []
        for m in [self._qwen_model, self._deepseek_model, self._active_model, _DEFAULT_PRIMARY] + _FALLBACK_CANDIDATES:
            if m and m not in models_to_try:
                models_to_try.append(m)

        for model in models_to_try:
            for client in clients:
                result = self._try_model(client, model, messages)
                if result is not None:
                    if model != self._active_model:
                        logger.info("[LLM] Active model selected: %s", model)
                        self._active_model = model
                    return result

        logger.warning("[LLM] All fallback models and providers exhausted.")
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

    @staticmethod
    def _truncate_to_single_bullet(
        text: str,
        original: str,
        other_project_names: Optional[List[str]] = None,
    ) -> str:
        """
        For experience/project bullet rewrites the LLM must produce ONE bullet.
        If it produces multiple paragraphs or continues past a clean sentence
        ending into what looks like a new project title, truncate ruthlessly.

        Strategy:
          1. Keep only the first non-empty paragraph (split on blank lines).
          2. Check sentences: if a subsequent sentence mentions other project names
             or tools not in the original text, truncate right before that sentence.
          3. Within the paragraph, if we detect a hard sentence boundary
             followed by a Title-Case noun phrase that is NOT in the original
             text, cut there — it means the model leaked the next project's name.
        """
        # Step 1: first paragraph only
        paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
        if not paragraphs:
            return text
        text = paragraphs[0]

        orig_lower = original.lower()

        # Step 2: If multiple sentences, check if sentence 2+ leaks other project info
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if len(sentences) > 1 and other_project_names:
            clean_sents = [sentences[0]]
            for sent in sentences[1:]:
                sent_lower = sent.lower()
                leaked = False
                for pname in other_project_names:
                    pname_clean = pname.strip().lower()
                    if len(pname_clean) > 3 and pname_clean in sent_lower and pname_clean not in orig_lower:
                        leaked = True
                        break
                    p_words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", pname) if w.lower() not in orig_lower]
                    if p_words and sum(1 for w in p_words if re.search(rf"\b{re.escape(w)}\b", sent_lower)) >= 2:
                        leaked = True
                        break
                if leaked:
                    logger.debug("[HF] Truncated bullet: dropped subsequent sentence leaking '%s'", sent[:40])
                    break
                clean_sents.append(sent)
            text = " ".join(clean_sents).strip()

        # Step 4: Truncate inline if another project's name appears inline
        if other_project_names:
            text_lower = text.lower()
            earliest_cut = -1
            for pname in other_project_names:
                pname_clean = pname.strip().lower()
                if len(pname_clean) > 3 and pname_clean in text_lower and pname_clean not in orig_lower:
                    idx = text_lower.find(pname_clean)
                    if earliest_cut == -1 or idx < earliest_cut:
                        earliest_cut = idx
            if earliest_cut > 10:
                cut_part = text[:earliest_cut].rstrip()
                cut_part = re.sub(
                    r'(?:;|,\s*(?:utilizing|leveraging|incorporating|for|and|while)|for\s+the|for|utilizing|leveraging|while|and)\s*$',
                    '',
                    cut_part,
                    flags=re.IGNORECASE,
                ).rstrip(" ,;-")
                if len(cut_part) > 15:
                    if not cut_part.endswith((".", "!", "?")):
                        cut_part += "."
                    text = cut_part
                    logger.debug("[HF] Truncated inline cross-project leak: '%s'", text[:50])

        return text.strip()

    @staticmethod
    def _contains_cross_project_contamination(
        suggested: str, original: str, other_project_names: Optional[List[str]] = None
    ) -> bool:
        """
        Return True if `suggested` contains words or title text from OTHER project
        names not present in `original`. Used to detect and reject cross-project
        bleed-through where the LLM copies text from an adjacent project entry.
        """
        if not other_project_names:
            return False
        orig_lower = original.lower()
        sugg_lower = suggested.lower()
        for pname in other_project_names:
            pname_clean = pname.strip().lower()
            if not pname_clean:
                continue
            # If the entire other project title appears in suggestion
            if len(pname_clean) > 4 and pname_clean in sugg_lower and pname_clean not in orig_lower:
                logger.warning(
                    "[HF] Cross-project contamination detected: full title '%s' in output.",
                    pname[:40],
                )
                return True
            pname_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", pname) if w.lower() not in orig_lower]
            if not pname_words:
                continue
            hits = sum(1 for w in set(pname_words) if re.search(rf"\b{re.escape(w.lower())}\b", sugg_lower))
            threshold = 2 if len(pname_words) >= 2 else 1
            if hits >= threshold:
                logger.warning(
                    "[HF] Cross-project contamination detected: %d words of '%s' in output.",
                    hits,
                    pname[:40],
                )
                return True
        return False

    def _clean_output(
        self,
        raw: str,
        original: str,
        task_type: str = "",
        other_project_names: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Post-process the model output.
        - Strip common artefacts (preambles, labels, tags, redundant markdown headers, leading quotes).
        - For experience/project bullets: truncate to a single clean bullet.
        - Detect and discard cross-project content bleed.
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

        # ── Single-bullet truncation guard ───────────────────────────────────
        # For experience bullets and project descriptions, the output MUST be
        # one bullet / one short paragraph.  If the LLM overruns into the next
        # project's content, truncate aggressively.
        if task_type in ("rewrite_experience", "rewrite_project", "improve_achievement"):
            text = self._truncate_to_single_bullet(text, original, other_project_names)

        # ── Cross-project contamination guard ────────────────────────────────
        # Discard the suggestion if it contains words from OTHER project titles.
        if other_project_names and self._contains_cross_project_contamination(
            text, original, other_project_names
        ):
            logger.warning("[HF] Discarding output: cross-project name contamination.")
            return None

        # Strip AI instructions, internal reasoning, and notes leakage
        text = sanitize_ai_text(text)
        if contains_ai_leakage(text):
            logger.warning("[HF] Output contained AI instruction/reasoning leakage, discarding.")
            return None

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
