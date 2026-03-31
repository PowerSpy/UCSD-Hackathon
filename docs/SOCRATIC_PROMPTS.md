# Socratic AI design

This document summarizes how the backend enforces **Socratic pedagogy** in code. Full prompt strings live in `backend/app/prompts.py`.

## Principles

1. **No direct answers** — The chat system prompt forbids giving final answers to exercises the student should solve. The model may offer strategies, smaller sub-problems, and metacognitive prompts (“Why do you think that?”).
2. **Grade-band scaffolding** — `K-5`, `6-8`, and `9-12` each get vocabulary and complexity constraints so explanations stay age-appropriate.
3. **Escalating hints** — `hint_level` (0–3) increases when the server detects frustration phrases in the student message (see `FRUSTRATION_PATTERNS` in `main.py`). At level 3+, the prompt explicitly allows a **more concrete hint** while still blocking verbatim final answers.
4. **Structured lessons** — Lesson JSON prompts require `intro` → `example` → `practice` style sections delivered sequentially; practice prompts must not include final answers.
5. **Quizzes** — Generated as JSON with mixed types; scoring on submit is rule-based (exact MC, fuzzy short answer) with **encouraging** feedback strings, not punitive copy.

## Offline / demo mode

If no API key is configured, `llm.py` returns short canned responses so the UI and API remain testable without external calls.

## Files

| File | Role |
|------|------|
| `backend/app/prompts.py` | System prompts for chat, lesson JSON, quiz JSON |
| `backend/app/llm.py` | OpenAI / Anthropic HTTP calls and JSON parsing |
| `backend/app/main.py` | Frustration detection, streaks, persistence |
