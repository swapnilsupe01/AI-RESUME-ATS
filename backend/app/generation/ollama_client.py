"""
Ollama Local LLM Client — Drop-in replacement / fallback for HuggingFaceClient.

Connects to a locally-running Ollama instance (default: http://localhost:11434)
and uses the same prompt templates, system message, and output cleaning pipeline
as the HuggingFaceClient so the ResumeUpgradeEngine can use it transparently.

Configuration:
  - OLLAMA_BASE_URL  (default: http://localhost:11434)
  - OLLAMA_MODEL     (default: auto-detect best available model)

Design:
  - Shares _SYSTEM_MSG and _USER_TEMPLATES from huggingface_client.py.
  - Reuses the same _clean_output, sanitize_ai_text, contains_ai_leakage pipeline.
  - Returns None on any failure so callers gracefully fall back to deterministic local upgrade.
  - Does NOT hallucinate: instructions explicitly forbid inventing data.
"""

import os
import re
import logging
from typing import Optional, Dict, Any, List

from app.generation.preservation_validator import (
    sanitize_ai_text,
    contains_ai_leakage,
)

logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Ollama-backed LLM client with the same interface as HuggingFaceClient.
    Returns None on any error so the caller can fall back to local generation.
    """

    def __init__(self):
        self._base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self._model: Optional[str] = os.getenv("OLLAMA_MODEL", "").strip() or None
        self._timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "300.0"))
        self._available: Optional[bool] = None  # cached after first check
        self._available_checked_at: float = 0.0  # timestamp of last check
        self._cache_ttl: float = 300.0           # re-check every 5 minutes
        self._detected_model: Optional[str] = None

    # ── Public API ────────────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Return True if Ollama is reachable and has at least one text model."""
        import time as _time
        now = _time.monotonic()
        if self._available is not None and (now - self._available_checked_at) < self._cache_ttl:
            return self._available
        try:
            import httpx
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    text_models = [m for m in models if "embed" not in m.get("name", "").lower()]
                    if text_models:
                        self._available = True
                        self._available_checked_at = now
                        if not self._model or self._model == "auto":
                            self._model = self._detect_best_model(text_models)
                        self._detected_model = self._model
                        return True
            self._available = False
            self._available_checked_at = now
        except Exception as exc:
            logger.debug("[Ollama] Connectivity check failed: %s", exc)
            self._available = False
            self._available_checked_at = now
        return self._available

    def is_available(self) -> bool:
        """Alias for is_configured — matches HuggingFaceClient interface."""
        return self.is_configured()

    def get_model_name(self) -> str:
        return f"ollama:{self._detected_model or self._model or 'unknown'}"

    def generate(
        self,
        task_type: str,
        original: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Call Ollama for the given task type, using the same prompt templates
        as HuggingFaceClient.

        Args:
            task_type: One of 'rewrite_summary', 'rewrite_experience',
                       'rewrite_project', 'tailor_to_jd', 'improve_achievement'.
            original:  The original text to improve.
            context:   Task-specific context values merged into the prompt template.

        Returns:
            Cleaned generated text string, or None on failure.
        """
        if not self.is_configured():
            logger.debug("[Ollama] Not available — skipping.")
            return None

        # Import prompt templates from huggingface_client (shared prompts)
        from app.generation.huggingface_client import _SYSTEM_MSG, _USER_TEMPLATES

        if task_type not in _USER_TEMPLATES:
            logger.warning("[Ollama] Unknown task_type: %s", task_type)
            return None

        ctx = context or {}

        # Extract cross-project contamination guard list (private key, not sent to LLM)
        other_proj_names = ctx.get("_other_project_names") or None

        # Clean context for template formatting (strip internal/private keys)
        fmt_ctx = {k: v for k, v in ctx.items() if not k.startswith("_")}

        # Ensure all template keys have defaults
        defaults = {
            "original": original,
            "jd_keywords": fmt_ctx.get("jd_keywords", ""),
            "candidate_tools": ", ".join(fmt_ctx.get("candidate_tools", []))
                               if isinstance(fmt_ctx.get("candidate_tools"), list)
                               else fmt_ctx.get("candidate_tools", ""),
            "technologies": ", ".join(fmt_ctx.get("technologies", []))
                            if isinstance(fmt_ctx.get("technologies"), list)
                            else fmt_ctx.get("technologies", ""),
            "jd_snippet": fmt_ctx.get("jd_snippet", ""),
            "rag_context": fmt_ctx.get("rag_context", ""),
        }

        template = _USER_TEMPLATES[task_type]
        try:
            user_msg = template.format(**defaults)
        except KeyError as exc:
            logger.warning("[Ollama] Prompt template key error: %s", exc)
            user_msg = f"Rewrite the following text professionally. Preserve all facts.\n\n{original}"

        raw = self._call_api(_SYSTEM_MSG, user_msg)
        if raw is None:
            return None

        return self._clean_output(
            raw, original, task_type=task_type, other_project_names=other_proj_names
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _detect_best_model(self, models: List[Dict[str, Any]]) -> str:
        """Select the best generative model from available Ollama models."""
        from app.ai.local_provider import MODEL_PREFERENCE_ORDER

        model_names = [m.get("name", "") for m in models]

        for pref in MODEL_PREFERENCE_ORDER:
            for installed in model_names:
                if pref in installed.lower():
                    return installed

        # Fallback to first available text model
        return model_names[0] if model_names else "gemma3:12b"

    def _call_api(self, system_msg: str, user_msg: str) -> Optional[str]:
        """Call Ollama's /api/chat endpoint with system and user messages."""
        try:
            import httpx
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": user_msg},
                        ],
                        "stream": False,
                        "think": False,          # Disable Gemma3/Qwen thinking mode
                        "keep_alive": "30m",
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 256,  # Increased to allow complete sentences
                        },
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    message = data.get("message", {})
                    raw_text = message.get("content", "")

                    # Strip <think>...</think> blocks emitted by reasoning models
                    # (Gemma3, Qwen3, DeepSeek-R1) before checking for empty output
                    text = re.sub(
                        r"<think>[\s\S]*?</think>",
                        "",
                        raw_text,
                        flags=re.IGNORECASE,
                    ).strip()

                    if text:
                        logger.debug("[Ollama] Got %d chars from model.", len(text))
                        return text
                    elif raw_text.strip():
                        # Content existed but was entirely inside <think> tags — model
                        # reasoning only, no final answer. Log and return None.
                        logger.warning(
                            "[Ollama] Response was pure reasoning (<think> only), no final answer."
                        )
                    else:
                        logger.warning(
                            "[Ollama] Model returned empty content (possible think-mode issue)."
                        )
                else:
                    logger.warning(
                        "[Ollama] API returned status %d: %s",
                        resp.status_code, resp.text[:200]
                    )
        except Exception as exc:
            logger.warning("[Ollama] Request failed: %s (%s)", type(exc).__name__, exc)
        return None

    def _clean_output(
        self,
        raw: str,
        original: str,
        task_type: str = "",
        other_project_names: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Post-process the model output — same logic as HuggingFaceClient._clean_output.
        """
        if not raw:
            return None

        text = raw

        # Remove conversational preambles
        text = re.sub(
            r"^(?:(?:Sure,?\s*)?(?:Here(?:'s|\s+is)|This\s+is|Below\s+is|A|An|The)\s+)?(?:the\s+)?(?:rewritten|improved|suggested|updated|new)?\s*(?:project\s+description|project\s+summary|project|bullet\s+point|bullet|summary|description|text|achievement|resume\s+bullet)?\s*:+\s*",
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

        # Remove markdown heading noise
        text = re.sub(r"\*\*(?:Key Contributions|Outcome|Key Highlights|Deliverables)\s*:?\*\*", "", text)

        # Strip secondary options or alternative suggestions
        alt_match = re.search(r"\b(?:Or,?\s+alternatively|Alternatively|Alternative\s*\d*|Option\s*2)\s*:\s*", text, flags=re.IGNORECASE)
        if alt_match:
            text = text[:alt_match.start()].strip()

        # Remove surrounding quotes
        if (text.startswith('"') and text.endswith('"')) or \
           (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()

        # Single-bullet truncation guard for experience/project tasks
        if task_type in ("rewrite_experience", "rewrite_project", "improve_achievement"):
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
            if paragraphs:
                text = paragraphs[0]

        # Strip AI instructions, internal reasoning, and notes leakage
        text = sanitize_ai_text(text)
        if contains_ai_leakage(text):
            logger.warning("[Ollama] Output contained AI instruction/reasoning leakage, discarding.")
            return None

        # Minimal quality gate
        if len(text) < 15:
            logger.warning("[Ollama] Output too short (%d chars), discarding.", len(text))
            return None

        if text.strip().lower() == original.strip().lower():
            logger.debug("[Ollama] Output identical to original, discarding.")
            return None

        return text.strip()


# Module-level singleton — loaded once per process
ollama_client = OllamaClient()
