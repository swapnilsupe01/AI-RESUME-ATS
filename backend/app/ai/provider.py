"""
AI Provider Base — Abstract contract for all writing assistant providers.
All providers must implement the same interface so the routing layer
can swap between Local (offline), OpenAI, and Gemini transparently.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AIProvider(ABC):
    """Abstract base class for AI writing assistant providers."""

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return a human-readable provider identifier."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider has valid credentials/dependencies."""
        ...

    @abstractmethod
    def optimize_bullet(
        self,
        bullet_text: str,
        mode: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimize a single resume bullet point.

        Args:
            bullet_text: The original bullet point text.
            mode: One of 'action_verb', 'star_metric', 'polish', 'jd_inject'.
            context: Optional dict with 'jd_keywords', 'role', 'industry', etc.

        Returns:
            {
                "original": str,
                "optimized": str,
                "mode": str,
                "changes": List[str],  # Human-readable change log
                "confidence": float    # 0.0 – 1.0
            }
        """
        ...

    @abstractmethod
    def live_keyword_audit(
        self,
        resume_text: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Perform a live keyword gap audit between a resume and job description.

        Returns:
            {
                "matched_keywords": List[str],
                "missing_critical": List[str],
                "missing_preferred": List[str],
                "keyword_density": float,
                "audit_score": float,
                "recommendations": List[str]
            }
        """
        ...

    @abstractmethod
    def tailor_resume(
        self,
        canonical_resume: Dict[str, Any],
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Generate a tailored version of a canonical resume for a specific job.
        """
        ...

    @abstractmethod
    def diagnose_cv_weaknesses(
        self,
        resume_text: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Diagnose weaknesses, weak action verbs, unquantified bullets, and keyword gaps.
        """
        ...

    @abstractmethod
    def transform_entire_resume(
        self,
        canonical_resume: Dict[str, Any],
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Transform an entire resume using RAG and local intelligence.
        """
        ...

    @abstractmethod
    def compare_cv_scores(
        self,
        original_text: str,
        enhanced_text: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """
        Compare ATS scores before and after enhancement against the target JD.
        """
        ...
