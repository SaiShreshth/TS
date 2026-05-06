import os
from typing import List


DEFAULT_MODEL = "gemini-3-flash"
DEFAULT_MAX_CONTEXT_CHARS = 6000


def _get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        import google.generativeai as genai
    except Exception:
        return None
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    try:
        return genai.GenerativeModel(model_name)
    except Exception:
        return None


def _truncate_context(parts: List[str]) -> str:
    max_chars = int(os.getenv("LLM_MAX_CONTEXT_CHARS", DEFAULT_MAX_CONTEXT_CHARS))
    joined = "\n".join(parts)
    if len(joined) <= max_chars:
        return joined
    truncated = joined[:max_chars]
    if "\n" in truncated:
        truncated = truncated.rsplit("\n", 1)[0]
    return truncated + "\n[truncated]"


def _fallback_explanation() -> str:
    return (
        "LLM explanation is unavailable. Set GEMINI_API_KEY to enable generated explanations. "
        "Review the retrieved context for supporting details."
    )


def _fallback_summary() -> str:
    return (
        "Summary is unavailable. Set GEMINI_API_KEY to enable generated summaries."
    )


def generate_explanation(query: str, context_parts: List[str]) -> str:
    if not context_parts:
        return "No explanation is available without supporting context."

    model = _get_gemini_model()
    if model is None:
        return _fallback_explanation()

    context_text = _truncate_context(context_parts)
    prompt = (
        "You are a legal assistant. Provide a concise explanation of the answer using only "
        "the provided context. If the context is insufficient, say so.\n\n"
        f"Question:\n{query}\n\nContext:\n{context_text}\n\n"
        "Write a 3-5 sentence explanation and reference sources when possible."
    )

    try:
        response = model.generate_content(prompt)
        content = getattr(response, "text", None)
        if content:
            return content.strip()
    except Exception:
        return _fallback_explanation()

    return _fallback_explanation()


def generate_summary(title: str, content_parts: List[str]) -> str:
    if not content_parts:
        return "No summary is available without document content."

    model = _get_gemini_model()
    if model is None:
        return _fallback_summary()

    context_text = _truncate_context(content_parts)
    prompt = (
        "You are a legal assistant. Summarize the document in 3-4 concise sentences. "
        "Focus on main obligations, constraints, or outcomes.\n\n"
        f"Document: {title}\n\nContent:\n{context_text}\n\n"
        "Write a short summary without bullet points."
    )

    try:
        response = model.generate_content(prompt)
        content = getattr(response, "text", None)
        if content:
            return content.strip()
    except Exception:
        return _fallback_summary()

    return _fallback_summary()
