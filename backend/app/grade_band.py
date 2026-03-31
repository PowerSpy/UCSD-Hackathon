"""Normalize K-12 grade bands used across chat, lessons, and quizzes."""

VALID_GRADE_BANDS = frozenset({"K-5", "6-8", "9-12"})
DEFAULT_GRADE_BAND = "6-8"


def normalize_grade_band(raw: str | None) -> str:
    if raw in VALID_GRADE_BANDS:
        return raw
    return DEFAULT_GRADE_BAND
