import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    grade_band: Mapped[str] = mapped_column(String(8), default="6-8")  # K-5, 6-8, 9-12
    display_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)


class LessonSession(Base):
    __tablename__ = "lesson_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id"))
    topic: Mapped[str] = mapped_column(String(512))
    grade_band: Mapped[str] = mapped_column(String(8))
    outline_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_index: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(default=False)
    failed_attempts_chat: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TopicProgress(Base):
    __tablename__ = "topic_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(64), ForeignKey("students.id"), index=True)
    topic_slug: Mapped[str] = mapped_column(String(256), index=True)
    topic_title: Mapped[str] = mapped_column(String(512))
    lessons_completed: Mapped[int] = mapped_column(Integer, default=0)
    hints_requested: Mapped[int] = mapped_column(Integer, default=0)
    quiz_scores_json: Mapped[str] = mapped_column(Text, default="[]")  # list of {score, at}
    last_quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prev_quiz_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lesson_incomplete: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def parse_json_list(s: str | None) -> list[Any]:
    if not s:
        return []
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return []
