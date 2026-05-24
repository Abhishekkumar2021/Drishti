"""Prompt templates for RAG generation (US-07.01)."""

from __future__ import annotations

RAG_SYSTEM_PROMPT = """You are Drishti, an expert codebase assistant. Answer questions using ONLY \
the provided context blocks.

Rules:
1. Cite every factual claim with the exact format [file_path:Lstart-end] matching the context tags.
2. If the context does not contain enough information, say so clearly.
3. Prefer concise, technical answers with short code references when helpful.
4. Do not invent files, symbols, or line numbers that are not in the context.
"""

_CITATION_FORMAT_NOTE = (
    "Use citations like [src/auth/token.py:L25-40] that match the context block headers."
)


def build_user_prompt(
    question: str,
    context_xml: str,
    *,
    conversation_prefix: str = "",
) -> str:
    """Assemble the user message with context and the question."""
    parts: list[str] = []
    if conversation_prefix.strip():
        parts.append(conversation_prefix.strip())
    parts.append("## Retrieved context")
    parts.append(context_xml)
    parts.append("## Question")
    parts.append(question.strip())
    parts.append(_CITATION_FORMAT_NOTE)
    return "\n\n".join(parts)
