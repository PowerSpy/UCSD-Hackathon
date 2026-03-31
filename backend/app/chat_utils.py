"""Shared chat frustration + lesson context logic for /chat and /chat/stream."""

import re
from typing import Any

from app.schemas import LessonContext

FRUSTRATION_PATTERNS = re.compile(
    r"\b(i\s*don'?t\s*know|idk|no\s*idea|too\s*hard|give\s*me\s*the\s*answer|just\s*tell\s*me|"
    r"i\s*can'?t|this\s*is\s*impossible|forget\s*it)\b",
    re.I,
)

CHAT_HISTORY_TURNS_MAX = 40


def detect_frustration(text: str) -> bool:
    return bool(FRUSTRATION_PATTERNS.search(text))


def hint_level_from_streak(n: int) -> int:
    return min(3, max(0, n))


def update_frustration_streak(state: dict[str, Any], message: str) -> None:
    if detect_frustration(message):
        state["failed_streak"] += 1
    elif len(message) > 40 and "?" in message:
        state["failed_streak"] = max(0, state["failed_streak"] - 1)


def lesson_context_text(lc: LessonContext | None) -> str | None:
    if not lc:
        return None
    ctx_parts = []
    if lc.topic:
        ctx_parts.append(f"Topic: {lc.topic}")
    if lc.section_title:
        ctx_parts.append(f"Section: {lc.section_title}")
    if lc.section_summary:
        ctx_parts.append(f"Summary: {lc.section_summary}")
    return "\n".join(ctx_parts) if ctx_parts else None


def append_chat_history(
    state: dict[str, Any], user_message: str, assistant_message: str
) -> None:
    state["messages"].append({"role": "user", "content": user_message})
    state["messages"].append({"role": "assistant", "content": assistant_message})
    if len(state["messages"]) > CHAT_HISTORY_TURNS_MAX:
        state["messages"] = state["messages"][-CHAT_HISTORY_TURNS_MAX:]
