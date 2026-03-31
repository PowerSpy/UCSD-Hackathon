import json
import re
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.config import settings
from app.prompts import (
    lesson_generation_system,
    lesson_next_system,
    quiz_generation_system,
    socratic_system_prompt,
)


def _openai_compat_credentials() -> tuple[str, str, str]:
    """Returns (api_key, base_url_without_trailing_slash, model) for OpenAI-compatible providers."""
    p = (settings.llm_provider or "zai").lower()
    if p == "zai":
        if not settings.zai_api_key:
            raise RuntimeError("ZAI_API_KEY is not set")
        return (
            settings.zai_api_key,
            settings.zai_base_url.rstrip("/"),
            settings.zai_model,
        )
    if p == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        return (
            settings.openai_api_key,
            settings.openai_base_url.rstrip("/"),
            settings.openai_model,
        )
    raise RuntimeError(
        f"llm_provider={settings.llm_provider!r} does not use OpenAI-compatible chat; use anthropic or set llm_provider to zai|openai"
    )


async def _openai_chat(messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    api_key, base, model = _openai_compat_credentials()
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]


async def _openai_chat_stream(
    messages: list[dict[str, str]], temperature: float = 0.7
) -> AsyncIterator[str]:
    """Stream text deltas from OpenAI-compatible chat completion (incl. Z.AI)."""
    api_key, base, model = _openai_compat_credentials()
    url = f"{base}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", url, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                raw = line[5:].strip()
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                for ch in chunk.get("choices") or []:
                    delta = ch.get("delta") or {}
                    piece = delta.get("content")
                    if piece:
                        yield piece


async def _anthropic_chat(system: str, messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.anthropic_model,
        "max_tokens": 4096,
        "system": system,
        "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
        "temperature": temperature,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(url, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
        blocks = data.get("content") or []
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text")


async def chat_complete(system: str, user: str, temperature: float = 0.7) -> str:
    if (settings.llm_provider or "").lower() == "anthropic":
        return await _anthropic_chat(system, [{"role": "user", "content": user}], temperature)
    return await _openai_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature,
    )


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def parse_json_response(text: str) -> dict[str, Any]:
    raw = _strip_json_fence(text)
    return json.loads(raw)


async def socratic_reply(
    *,
    grade_band: str,
    user_message: str,
    lesson_context: str | None,
    hint_level: int,
    history: list[dict[str, str]] | None = None,
) -> str:
    system = socratic_system_prompt(grade_band, hint_level=hint_level)
    parts = []
    if lesson_context:
        parts.append(f"Current lesson context (for alignment, do not repeat verbatim):\n{lesson_context}\n")
    parts.append(f"Student message:\n{user_message}")
    user_content = "\n".join(parts)

    if (settings.llm_provider or "").lower() == "anthropic":
        msgs: list[dict[str, str]] = []
        if history:
            for h in history[-8:]:
                msgs.append({"role": h["role"], "content": h["content"]})
        msgs.append({"role": "user", "content": user_content})
        return await _anthropic_chat(system, msgs, temperature=0.6)

    openai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if history:
        for h in history[-8:]:
            openai_messages.append({"role": h["role"], "content": h["content"]})
    openai_messages.append({"role": "user", "content": user_content})
    return await _openai_chat(openai_messages, temperature=0.6)


async def socratic_reply_stream(
    *,
    grade_band: str,
    user_message: str,
    lesson_context: str | None,
    hint_level: int,
    history: list[dict[str, str]] | None = None,
) -> AsyncIterator[str]:
    system = socratic_system_prompt(grade_band, hint_level=hint_level)
    parts = []
    if lesson_context:
        parts.append(
            f"Current lesson context (for alignment, do not repeat verbatim):\n{lesson_context}\n"
        )
    parts.append(f"Student message:\n{user_message}")
    user_content = "\n".join(parts)

    try:
        if (settings.llm_provider or "").lower() == "anthropic":
            msgs: list[dict[str, str]] = []
            if history:
                for h in history[-8:]:
                    msgs.append({"role": h["role"], "content": h["content"]})
            msgs.append({"role": "user", "content": user_content})
            text = await _anthropic_chat(system, msgs, temperature=0.6)
            yield text
            return

        openai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        if history:
            for h in history[-8:]:
                openai_messages.append({"role": h["role"], "content": h["content"]})
        openai_messages.append({"role": "user", "content": user_content})
        async for piece in _openai_chat_stream(openai_messages, temperature=0.6):
            yield piece
    except (RuntimeError, httpx.HTTPError, httpx.StreamError):
        yield offline_socratic_fallback(grade_band, hint_level)


async def generate_first_lesson_section(topic: str, grade_band: str) -> dict[str, Any]:
    system = lesson_generation_system(grade_band)
    user = f'Topic: "{topic}"\nProduce the first section only (intro). Include full outline for the whole lesson in "outline".'
    text = await chat_complete(system, user, temperature=0.5)
    return parse_json_response(text)


async def generate_next_lesson_section(
    topic: str,
    grade_band: str,
    outline: list[str],
    prior_sections_summary: str,
    index: int,
) -> dict[str, Any]:
    system = lesson_next_system(grade_band)
    user = (
        f'Topic: "{topic}"\nOutline: {json.dumps(outline)}\n'
        f"Next section index (0-based): {index}\n"
        f"Prior sections summary:\n{prior_sections_summary}\n"
        f"Generate the section at this index. Set is_last_section when this is the final outline step."
    )
    text = await chat_complete(system, user, temperature=0.5)
    return parse_json_response(text)


async def generate_quiz(topic: str, grade_band: str, performance_note: str | None = None) -> dict[str, Any]:
    system = quiz_generation_system(grade_band, topic)
    user = f'Generate the quiz for topic "{topic}".'
    if performance_note:
        user += f"\nAdapt difficulty slightly using this note: {performance_note}"
    text = await chat_complete(system, user, temperature=0.4)
    return parse_json_response(text)


def offline_socratic_fallback(grade_band: str, hint_level: int) -> str:
    return (
        f"[Demo mode — set ZAI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY] "
        f"I'm your Socratic tutor ({grade_band}). What part feels unclear so far — the words, the steps, or where to start? "
        f"Try naming one thing you notice about the problem. "
        + ("Here's a gentler angle: break the question into two smaller questions. What's the first small piece? " if hint_level >= 3 else "")
    )


def offline_lesson_fallback(topic: str) -> dict[str, Any]:
    return {
        "title": topic,
        "outline": ["Introduction", "Example", "Guided practice"],
        "section": {
            "type": "intro",
            "title": "Introduction",
            "body": f"Welcome! We'll explore **{topic}** step by step.\n\nWhat do you already know about this topic in one sentence?",
            "practice_prompt": None,
        },
    }


def offline_quiz_fallback(topic: str) -> dict[str, Any]:
    return {
        "questions": [
            {
                "id": "q1",
                "type": "multiple_choice",
                "prompt": f"Which best describes a goal of learning about {topic}?",
                "choices": [
                    "Memorize without understanding",
                    "Build understanding you can explain",
                    "Skip practice",
                    "Avoid questions",
                ],
                "correct": "Build understanding you can explain",
            },
            {
                "id": "q2",
                "type": "short_answer",
                "prompt": "In your own words, why is asking questions useful while learning?",
                "choices": None,
                "correct": "understanding",
            },
        ]
    }
