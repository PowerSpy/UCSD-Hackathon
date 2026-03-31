from typing import Any, Literal

from pydantic import BaseModel, Field


GradeBand = Literal["K-5", "6-8", "9-12"]


class LessonContext(BaseModel):
    topic: str | None = None
    section_title: str | None = None
    section_summary: str | None = None


class ChatRequest(BaseModel):
    message: str
    session_id: str
    grade_level: str = "6-8"
    lesson_context: LessonContext | None = None


class ChatResponse(BaseModel):
    response: str
    lesson_generated: bool = False
    lesson_data: dict[str, Any] | None = None
    hint_level: int = 0
    frustration_detected: bool = False


class LessonGenerateRequest(BaseModel):
    topic: str
    grade_level: str = "6-8"
    session_id: str
    student_id: str | None = None


class LessonGenerateResponse(BaseModel):
    session_id: str
    topic: str
    title: str
    outline: list[str]
    section: dict[str, Any]
    section_index: int
    total_sections: int


class LessonNextRequest(BaseModel):
    session_id: str
    completed_section_index: int
    student_id: str | None = None


class LessonNextResponse(BaseModel):
    section: dict[str, Any]
    section_index: int
    total_sections: int
    lesson_complete: bool


class QuizGenerateRequest(BaseModel):
    topic: str
    grade_level: str = "6-8"
    session_id: str | None = None
    student_id: str | None = None
    prior_performance: str | None = None


class QuizGenerateResponse(BaseModel):
    topic: str
    questions: list[dict[str, Any]]


class QuizSubmitRequest(BaseModel):
    topic: str
    grade_level: str = "6-8"
    student_id: str | None = None
    answers: dict[str, str] = Field(default_factory=dict)  # question_id -> answer text
    questions: list[dict[str, Any]] = Field(default_factory=list)


class QuizSubmitResponse(BaseModel):
    score_percent: int
    correct: int
    total: int
    feedback: list[dict[str, Any]]


class ProgressTopic(BaseModel):
    topic_slug: str
    topic_title: str
    lessons_completed: int
    hints_requested: int
    last_quiz_score: int | None = None
    prev_quiz_score: int | None = None
    lesson_incomplete: bool = False


class ProgressGetResponse(BaseModel):
    student_id: str
    grade_band: str
    current_streak: int
    topics_this_week: list[str]
    topics: list[ProgressTopic]
    incomplete_lesson_nudge: str | None = None


class ProgressUpdateBody(BaseModel):
    grade_band: str | None = None
    hints_increment: int = 0
    topic_slug: str | None = None
    topic_title: str | None = None
