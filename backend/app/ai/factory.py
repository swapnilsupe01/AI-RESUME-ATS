"""
Provider Factory — Selects the best available AI provider at runtime.
Priority: Gemini > OpenAI > Local (offline fallback — always works).
"""
import os
from typing import Optional
from app.ai.provider import AIProvider
from app.ai.local_provider import LocalAIProvider

_active_provider: Optional[AIProvider] = None


def get_provider() -> AIProvider:
    """
    Return the best available AI provider.
    Lazy-loads and caches the provider instance.
    """
    global _active_provider

    if _active_provider is not None and _active_provider.is_available():
        return _active_provider

    # Try Gemini first
    if os.getenv("GEMINI_API_KEY", "").strip():
        try:
            from app.ai.gemini_provider import GeminiProvider
            provider = GeminiProvider()
            if provider.is_available():
                _active_provider = provider
                return _active_provider
        except Exception:
            pass

    # Try OpenAI next
    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            from app.ai.openai_provider import OpenAIProvider
            provider = OpenAIProvider()
            if provider.is_available():
                _active_provider = provider
                return _active_provider
        except Exception:
            pass

    # Local offline fallback — always available
    _active_provider = LocalAIProvider()
    return _active_provider


def reset_provider():
    """Force provider re-selection (e.g., after credentials update)."""
    global _active_provider
    _active_provider = None
