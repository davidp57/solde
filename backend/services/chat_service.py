"""Chat service — AI assistant via Google Gemini (or OpenAI), with SSE streaming."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.app_settings import AppSettings
from backend.models.chat_log import ChatLog

if TYPE_CHECKING:
    from backend.models.user import User

logger = logging.getLogger(__name__)

_SETTINGS_ID = 1
_DOC_ROOT = Path(__file__).resolve().parents[2] / "doc"


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    """Load and cache the system prompt from doc/llm/reference.md + doc/user/manuel.md."""
    parts: list[str] = []
    for path in (_DOC_ROOT / "llm" / "reference.md", _DOC_ROOT / "user" / "manuel.md"):
        if path.exists():
            parts.append(path.read_text(encoding="utf-8"))
        else:
            logger.warning("Chat system prompt file not found: %s", path)
    return "\n\n---\n\n".join(parts)


async def _get_chat_settings(db: AsyncSession) -> tuple[str, str | None, str | None]:
    """Return (provider, api_key, model) from AppSettings."""
    result = await db.execute(
        select(
            AppSettings.chat_provider,
            AppSettings.chat_api_key,
            AppSettings.chat_model,
        ).where(AppSettings.id == _SETTINGS_ID)
    )
    row = result.one_or_none()
    if row is None:
        return "gemini", None, None
    return row.chat_provider, row.chat_api_key, row.chat_model


def _default_model(provider: str) -> str:
    if provider == "openai":
        return "gpt-4o-mini"
    return "gemini-1.5-flash"


def _to_gemini_contents(messages: list[dict[str, str]]) -> list[dict[str, object]]:
    """Convert [{role, content}] to Gemini contents format."""
    role_map = {"user": "user", "assistant": "model"}
    return [
        {"role": role_map.get(m["role"], "user"), "parts": [{"text": m["content"]}]}
        for m in messages
    ]


async def stream_chat(
    messages: list[dict[str, str]],
    user: User,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Stream SSE chunks from the configured AI provider, then log the question."""
    provider, api_key, model_name = await _get_chat_settings(db)

    if not api_key:
        yield _sse({"error": "Chat non configuré. Contactez l'administrateur."})
        yield _sse("[DONE]")
        return

    system_prompt = _load_system_prompt()
    model_name = model_name or _default_model(provider)

    # Extract the last user question for logging
    last_question = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")

    prompt_tokens: int | None = None
    completion_tokens: int | None = None

    try:
        if provider == "gemini":
            async for chunk, usage in _stream_gemini(api_key, model_name, system_prompt, messages):
                yield _sse({"text": chunk})
                if usage:
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
        elif provider == "openai":
            async for chunk, usage in _stream_openai(api_key, model_name, system_prompt, messages):
                yield _sse({"text": chunk})
                if usage:
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
        else:
            yield _sse({"error": f"Fournisseur inconnu : {provider}"})
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat streaming error")
        exc_str = str(exc)
        is_quota = "429" in exc_str or "quota" in exc_str.lower()
        is_quota = is_quota or "ResourceExhausted" in type(exc).__name__
        is_auth = "401" in exc_str or "403" in exc_str
        is_auth = is_auth or "API_KEY" in exc_str.upper() or "invalid" in exc_str.lower()
        if is_quota:
            msg = (
                "Quota API dépassé. Réessayez dans quelques instants"
                " ou vérifiez votre plan sur ai.dev/rate-limit."
            )
        elif is_auth:
            msg = (
                "Clé API invalide ou non autorisée."
                " Vérifiez la configuration dans les Paramètres."
            )
        else:
            msg = "Erreur lors de la génération de la réponse."
        yield _sse({"error": msg})
        logger.debug("Original exception: %s", exc)

    yield _sse("[DONE]")

    # Log the question (fire-and-forget; errors are non-fatal)
    try:
        log_entry = ChatLog(
            user_id=user.id,
            question=last_question,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
        db.add(log_entry)
        await db.commit()
    except Exception:  # noqa: BLE001
        logger.exception("Failed to log chat question")


def _sse(data: object) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"data: {payload}\n\n"


async def _stream_gemini(
    api_key: str,
    model_name: str,
    system_prompt: str,
    messages: list[dict[str, str]],
) -> AsyncIterator[tuple[str, dict[str, int] | None]]:
    import google.generativeai as genai  # noqa: PLC0415

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
    )
    contents = _to_gemini_contents(messages)
    response = await model.generate_content_async(contents, stream=True)
    async for chunk in response:
        text = chunk.text if hasattr(chunk, "text") and chunk.text else ""
        if text:
            yield text, None
    # Try to extract token usage from the final response
    try:
        usage_meta = response.usage_metadata
        yield (
            "",
            {
                "prompt_tokens": usage_meta.prompt_token_count,
                "completion_tokens": usage_meta.candidates_token_count,
            },
        )
    except Exception:  # noqa: BLE001
        pass


async def _stream_openai(
    api_key: str,
    model_name: str,
    system_prompt: str,
    messages: list[dict[str, str]],
) -> AsyncIterator[tuple[str, dict[str, int] | None]]:
    from openai import AsyncOpenAI  # noqa: PLC0415

    client = AsyncOpenAI(api_key=api_key)
    openai_messages = [{"role": "system", "content": system_prompt}] + messages
    stream = await client.chat.completions.create(
        model=model_name,
        messages=openai_messages,
        stream=True,
    )
    async for event in stream:
        delta = event.choices[0].delta if event.choices else None
        if delta and delta.content:
            yield delta.content, None
