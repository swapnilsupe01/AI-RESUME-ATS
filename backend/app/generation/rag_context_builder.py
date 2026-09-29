"""
RAG Context Builder — Layer E AI Resume Upgrade Engine.

Assembles retrieved guidance chunks into a concise evidence block
that is injected into the Hugging Face prompt as grounding context.

Design:
  - Calls rag_retriever.retrieve_guidance() to get top-k chunks.
  - Deduplicates by source file so one doc doesn't dominate.
  - Returns a plain-text block the HF prompt template can embed directly.
  - Fails silently (returns "") so the caller always gets a string.

This module is intentionally thin. It does NOT call the HF model
and does NOT modify any suggestion objects.
"""

from __future__ import annotations

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Maximum characters of guidance to inject per prompt (keeps tokens bounded)
_MAX_CONTEXT_CHARS = 1200
_TOP_K = 4


def build_rag_context(
    query: str,
    top_k: int = _TOP_K,
    max_chars: int = _MAX_CONTEXT_CHARS,
) -> str:
    """
    Retrieve relevant guidance chunks for `query` and format them
    as an evidence block for the HF prompt.

    Args:
        query:     The bullet / summary text being improved.
        top_k:     Number of chunks to retrieve.
        max_chars: Hard cap on total injected guidance characters.

    Returns:
        A formatted string like:
            GUIDANCE CONTEXT (from your knowledge base):
            [1] <chunk text…>   (source: general_ats_rules.md)
            [2] <chunk text…>   (source: backend_roles.md)

        Or "" if the vector store is empty or retrieval fails.
    """
    try:
        from app.generation.rag_retriever import retrieve_guidance  # lazy import
        chunks = retrieve_guidance(query, top_k=top_k)
    except Exception as exc:
        logger.debug("[RAG] Retriever unavailable: %s — skipping context.", exc)
        return ""

    if not chunks:
        return ""

    # Deduplicate: keep at most 2 chunks from the same source doc
    seen_sources: dict[str, int] = {}
    deduplicated: List[dict] = []
    for chunk in chunks:
        src = chunk.get("source", "unknown")
        count = seen_sources.get(src, 0)
        if count < 2:
            deduplicated.append(chunk)
            seen_sources[src] = count + 1

    # Build evidence block with character cap
    lines: List[str] = ["GUIDANCE CONTEXT (from resume knowledge base):"]
    used = 0
    for i, chunk in enumerate(deduplicated, start=1):
        text   = (chunk.get("text") or "").strip()
        source = chunk.get("source", "unknown")
        if not text:
            continue
        entry = f"[{i}] {text}  (source: {source})"
        if used + len(entry) > max_chars:
            break
        lines.append(entry)
        used += len(entry)

    if len(lines) == 1:
        # Only header, no real content
        return ""

    return "\n".join(lines) + "\n\n"
