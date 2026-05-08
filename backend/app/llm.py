import os
import logging
from typing import Any, List


DEFAULT_MODEL = "gemini-3-flash"
DEFAULT_MAX_CONTEXT_CHARS = 6000
DEFAULT_MAX_CHAT_MESSAGES = 8

LEGAL_ASSISTANT_PROMPT = (
    "You are a legal document assistant. Answer using only the retrieved context "
    "and prior chat messages. If the context is insufficient, say so and ask for the "
    "missing document or clause. Do not invent facts. Do not provide legal advice; "
    "provide informational analysis only. Cite sources using square brackets with the "
    "source tags shown in the context (for example, [pdf:filename:3])."
)

logger = logging.getLogger("app.llm")


def _get_gemini_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY missing. Check .env loading.")
        return None
    try:
        import google.generativeai as genai
    except Exception:
        logger.exception("Failed to import google.generativeai.")
        return None
    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    try:
        model = genai.GenerativeModel(model_name)
        logger.info("Gemini model initialized: %s", model_name)
        return model
    except Exception:
        logger.exception("Failed to initialize Gemini model: %s", model_name)
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


def _fallback_answer() -> str:
    return (
        "LLM answer is unavailable. Set GEMINI_API_KEY to enable generated answers. "
        "Review the retrieved context for supporting details."
    )


def _fallback_summary() -> str:
    return (
        "Summary is unavailable. Set GEMINI_API_KEY to enable generated summaries."
    )


def _extract_response_text(response: Any) -> str | None:
    if response is None:
        return None
    text = getattr(response, "text", None)
    if text:
        return text
    candidates = getattr(response, "candidates", None)
    if not candidates:
        return None
    content = getattr(candidates[0], "content", None)
    if content is None:
        return None
    parts = getattr(content, "parts", None) or []
    chunks = []
    for part in parts:
        part_text = getattr(part, "text", None)
        if part_text:
            chunks.append(part_text)
    return "".join(chunks) if chunks else None


def _normalize_chat_messages(chat_messages: List[Any] | None) -> List[dict]:
    if not chat_messages:
        return []
    max_messages = int(os.getenv("LLM_MAX_CHAT_MESSAGES", DEFAULT_MAX_CHAT_MESSAGES))
    if max_messages > 0:
        chat_messages = chat_messages[-max_messages:]
    normalized = []
    for message in chat_messages:
        if isinstance(message, dict):
            role = str(message.get("role", "")).lower()
            text = str(message.get("text", "")).strip()
        else:
            role = str(getattr(message, "role", "")).lower()
            text = str(getattr(message, "text", "")).strip()
        if not text:
            continue
        if role == "user":
            normalized.append({"role": "user", "parts": [text]})
        elif role in ("assistant", "model"):
            normalized.append({"role": "model", "parts": [text]})
    return normalized


def _build_answer_prompt(question: str, context_text: str) -> str:
    return (
        f"{LEGAL_ASSISTANT_PROMPT}\n\n"
        f"User question:\n{question}\n\n"
        f"Retrieved context:\n{context_text}\n\n"
        "Answer in 3-6 concise sentences."
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
        content = _extract_response_text(response)
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
        content = _extract_response_text(response)
        if content:
            return content.strip()
    except Exception:
        return _fallback_summary()

    return _fallback_summary()


def generate_chat_answer(
    question: str,
    chat_messages: List[Any] | None,
    context_parts: List[str],
) -> str:
    if not context_parts:
        return "No answer is available without supporting context."

    model = _get_gemini_model()
    if model is None:
        return _fallback_answer()

    context_text = _truncate_context(context_parts)
    prompt = _build_answer_prompt(question, context_text)
    history = _normalize_chat_messages(chat_messages)

    try:
        if history:
            contents = history + [{"role": "user", "parts": [prompt]}]
            response = model.generate_content(contents)
        else:
            response = model.generate_content(prompt)
        content = _extract_response_text(response)
        if content:
            return content.strip()
    except Exception:
        return _fallback_answer()

    return _fallback_answer()
