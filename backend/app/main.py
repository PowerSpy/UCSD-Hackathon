import json
import re
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import llm
from app.models import Student, LessonSession, TopicProgress, parse_json_list
from app.schemas import (
    ChatRequest,
    ChatResponse,
    LessonGenerateRequest,
    LessonGenerateResponse,
    LessonNextRequest,
    LessonNextResponse,
    ProgressGetResponse,
    ProgressTopic,
    ProgressUpdateBody,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)

app = FastAPI(title="Socratic Learning Companion API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ephemeral chat state: session_id -> { messages, failed_streak }
CHAT_STATE: dict[str, dict[str, Any]] = {}


def _ensure_tables():
    Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup():
    _ensure_tables()


@app.get("/health")
def health():
    return {"status": "ok"}


FRUSTRATION_PATTERNS = re.compile(
    r"\b(i\s*don'?t\s*know|idk|no\s*idea|too\s*hard|give\s*me\s*the\s*answer|just\s*tell\s*me|"
    r"i\s*can'?t|this\s*is\s*impossible|forget\s*it)\b",
    re.I,
)


def _detect_frustration(text: str) -> bool:
    return bool(FRUSTRATION_PATTERNS.search(text))


def _hint_level_from_streak(n: int) -> int:
    return min(3, max(0, n))


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _slug(topic: str) -> str:
    t = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return t[:200] or "topic"


def _ensure_student(db: Session, student_id: str, grade_band: str) -> Student:
    s = db.get(Student, student_id)
    if not s:
        s = Student(id=student_id, grade_band=grade_band)
        db.add(s)
        db.commit()
        db.refresh(s)
    elif grade_band and s.grade_band != grade_band:
        s.grade_band = grade_band
        db.commit()
        db.refresh(s)
    return s


def _update_streak(db: Session, student: Student):
    today = date.today()
    if student.last_active_date is None:
        student.current_streak = 1
    elif student.last_active_date == today:
        pass
    elif student.last_active_date == today - timedelta(days=1):
        student.current_streak += 1
    else:
        student.current_streak = 1
    student.last_active_date = today
    db.commit()


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(body: ChatRequest, db: Session = Depends(get_db)):
    grade = body.grade_level if body.grade_level in ("K-5", "6-8", "9-12") else "6-8"
    sid = body.session_id
    state = CHAT_STATE.setdefault(sid, {"messages": [], "failed_streak": 0})

    if _detect_frustration(body.message):
        state["failed_streak"] += 1
    else:
        # small decay on constructive messages
        if len(body.message) > 40 and "?" in body.message:
            state["failed_streak"] = max(0, state["failed_streak"] - 1)

    hint_level = _hint_level_from_streak(state["failed_streak"])
    frustration = state["failed_streak"] >= 3

    ctx_parts = []
    if body.lesson_context:
        lc = body.lesson_context
        if lc.topic:
            ctx_parts.append(f"Topic: {lc.topic}")
        if lc.section_title:
            ctx_parts.append(f"Section: {lc.section_title}")
        if lc.section_summary:
            ctx_parts.append(f"Summary: {lc.section_summary}")
    lesson_context = "\n".join(ctx_parts) if ctx_parts else None

    history = state["messages"]

    try:
        text = await llm.socratic_reply(
            grade_band=grade,
            user_message=body.message,
            lesson_context=lesson_context,
            hint_level=hint_level,
            history=history,
        )
    except RuntimeError:
        text = llm.offline_socratic_fallback(grade, hint_level)

    state["messages"].append({"role": "user", "content": body.message})
    state["messages"].append({"role": "assistant", "content": text})
    if len(state["messages"]) > 40:
        state["messages"] = state["messages"][-40:]

    return ChatResponse(
        response=text,
        lesson_generated=False,
        lesson_data=None,
        hint_level=hint_level,
        frustration_detected=frustration,
    )


@app.post("/lesson/generate", response_model=LessonGenerateResponse)
async def lesson_generate(body: LessonGenerateRequest, db: Session = Depends(get_db)):
    grade = body.grade_level if body.grade_level in ("K-5", "6-8", "9-12") else "6-8"
    student_id = body.student_id or "anonymous"
    _ensure_student(db, student_id, grade)

    try:
        data = await llm.generate_first_lesson_section(body.topic.strip(), grade)
    except Exception:
        data = llm.offline_lesson_fallback(body.topic.strip())

    title = data.get("title") or body.topic
    outline = data.get("outline") or ["Introduction", "Example", "Guided practice"]
    section = data.get("section") or {}
    if not isinstance(outline, list):
        outline = ["Introduction", "Example", "Guided practice"]

    session_id = body.session_id or str(uuid.uuid4())
    sections = [section]
    row = LessonSession(
        session_id=session_id,
        student_id=student_id,
        topic=body.topic.strip(),
        grade_band=grade,
        outline_json=json.dumps(outline),
        sections_json=json.dumps(sections),
        current_index=0,
        completed=False,
        failed_attempts_chat=0,
    )
    db.merge(row)

    slug = _slug(body.topic)
    tp = db.query(TopicProgress).filter_by(student_id=student_id, topic_slug=slug).first()
    if not tp:
        tp = TopicProgress(
            student_id=student_id,
            topic_slug=slug,
            topic_title=title,
            lesson_incomplete=True,
        )
        db.add(tp)
    else:
        tp.lesson_incomplete = True
        tp.topic_title = title
    db.commit()

    return LessonGenerateResponse(
        session_id=session_id,
        topic=body.topic.strip(),
        title=title,
        outline=outline,
        section=section,
        section_index=0,
        total_sections=len(outline),
    )


@app.post("/lesson/next", response_model=LessonNextResponse)
async def lesson_next(body: LessonNextRequest, db: Session = Depends(get_db)):
    row = db.query(LessonSession).filter_by(session_id=body.session_id).first()
    if not row:
        raise HTTPException(404, "Session not found")

    outline = json.loads(row.outline_json or "[]")
    sections = json.loads(row.sections_json or "[]")
    idx = body.completed_section_index + 1
    if idx >= len(outline):
        row.completed = True
        row.current_index = len(outline) - 1
        db.commit()
        if body.student_id:
            slug = _slug(row.topic)
            tp = db.query(TopicProgress).filter_by(student_id=body.student_id, topic_slug=slug).first()
            if tp:
                tp.lesson_incomplete = False
                tp.lessons_completed += 1
                db.commit()
        return LessonNextResponse(
            section={"type": "done", "title": "Lesson complete", "body": "Great work!", "practice_prompt": None},
            section_index=len(outline) - 1,
            total_sections=len(outline),
            lesson_complete=True,
        )

    prior_summary = "\n".join(
        f"- {s.get('title', 'section')}: {(s.get('body') or '')[:400]}" for s in sections
    )
    try:
        data = await llm.generate_next_lesson_section(
            row.topic, row.grade_band, outline, prior_summary, idx
        )
    except Exception:
        data = {
            "section": {
                "type": "practice" if idx == len(outline) - 1 else "example",
                "title": outline[idx] if idx < len(outline) else "Continue",
                "body": f"Let's keep going with **{row.topic}**. What pattern do you notice from the last part?",
                "practice_prompt": "Explain one idea from this lesson in your own words.",
            },
            "is_last_section": idx >= len(outline) - 1,
        }

    new_section = data.get("section") or {}
    is_last = bool(data.get("is_last_section")) or idx >= len(outline) - 1
    sections.append(new_section)
    row.sections_json = json.dumps(sections)
    row.current_index = idx
    row.completed = False
    db.commit()

    return LessonNextResponse(
        section=new_section,
        section_index=idx,
        total_sections=len(outline),
        lesson_complete=is_last,
    )


@app.post("/quiz/generate", response_model=QuizGenerateResponse)
async def quiz_generate(body: QuizGenerateRequest, db: Session = Depends(get_db)):
    grade = body.grade_level if body.grade_level in ("K-5", "6-8", "9-12") else "6-8"
    perf = body.prior_performance
    try:
        data = await llm.generate_quiz(body.topic.strip(), grade, perf)
    except Exception:
        data = llm.offline_quiz_fallback(body.topic.strip())
    questions = data.get("questions") or []
    return QuizGenerateResponse(topic=body.topic.strip(), questions=questions)


def _score_question(q: dict[str, Any], answer: str) -> tuple[bool, str]:
    qtype = q.get("type") or "short_answer"
    correct = q.get("correct") or ""
    if qtype == "multiple_choice":
        ok = _normalize(answer) == _normalize(str(correct))
        return ok, "Nice!" if ok else "Think about which choice best matches what you learned."
    if qtype == "fill_blank":
        ok = _normalize(answer) == _normalize(str(correct))
        return ok, "Exactly." if ok else "Close — compare your wording to the key idea."
    # short_answer: allow substring match
    a = _normalize(answer)
    key = _normalize(str(correct))
    ok = len(a) > 0 and (key in a or a in key or any(w in a for w in key.split() if len(w) > 4))
    return ok, "Good reasoning." if ok else "Try connecting your answer to the main definition from the lesson."


@app.post("/quiz/submit", response_model=QuizSubmitResponse)
async def quiz_submit(body: QuizSubmitRequest, db: Session = Depends(get_db)):
    grade = body.grade_level if body.grade_level in ("K-5", "6-8", "9-12") else "6-8"
    student_id = body.student_id or "anonymous"
    st = _ensure_student(db, student_id, grade)
    _update_streak(db, st)

    questions = body.questions or []
    feedback: list[dict[str, Any]] = []
    correct_n = 0
    for q in questions:
        qid = str(q.get("id") or "")
        ans = body.answers.get(qid, "")
        ok, tip = _score_question(q, ans)
        if ok:
            correct_n += 1
        feedback.append({"question_id": qid, "correct": ok, "encouragement": tip})

    total = len(questions) or 1
    pct = int(round(100 * correct_n / total))

    slug = _slug(body.topic)
    tp = db.query(TopicProgress).filter_by(student_id=student_id, topic_slug=slug).first()
    if not tp:
        tp = TopicProgress(
            student_id=student_id,
            topic_slug=slug,
            topic_title=body.topic,
            quiz_scores_json="[]",
        )
        db.add(tp)
    scores = parse_json_list(tp.quiz_scores_json)
    scores.append({"score": pct, "at": datetime.utcnow().isoformat() + "Z"})
    tp.prev_quiz_score = tp.last_quiz_score
    tp.last_quiz_score = pct
    tp.quiz_scores_json = json.dumps(scores[-20:])
    db.commit()

    return QuizSubmitResponse(
        score_percent=pct,
        correct=correct_n,
        total=len(questions),
        feedback=feedback,
    )


@app.get("/progress/{student_id}", response_model=ProgressGetResponse)
def progress_get(student_id: str, db: Session = Depends(get_db)):
    st = db.get(Student, student_id)
    if not st:
        return ProgressGetResponse(
            student_id=student_id,
            grade_band="6-8",
            current_streak=0,
            topics_this_week=[],
            topics=[],
            incomplete_lesson_nudge=None,
        )

    week_ago = date.today() - timedelta(days=7)
    topics = db.query(TopicProgress).filter_by(student_id=student_id).all()
    topics_week: list[str] = []
    out: list[ProgressTopic] = []
    nudge: str | None = None
    for tp in topics:
        if tp.updated_at and tp.updated_at.date() >= week_ago:
            topics_week.append(tp.topic_title)
        out.append(
            ProgressTopic(
                topic_slug=tp.topic_slug,
                topic_title=tp.topic_title,
                lessons_completed=tp.lessons_completed,
                hints_requested=tp.hints_requested,
                last_quiz_score=tp.last_quiz_score,
                prev_quiz_score=tp.prev_quiz_score,
                lesson_incomplete=tp.lesson_incomplete,
            )
        )
        if tp.lesson_incomplete and not nudge:
            nudge = f"You have an unfinished lesson: {tp.topic_title}. Want to pick it up?"

    return ProgressGetResponse(
        student_id=student_id,
        grade_band=st.grade_band,
        current_streak=st.current_streak,
        topics_this_week=sorted(set(topics_week)),
        topics=out,
        incomplete_lesson_nudge=nudge,
    )


@app.post("/progress/{student_id}", response_model=ProgressGetResponse)
def progress_post(student_id: str, body: ProgressUpdateBody, db: Session = Depends(get_db)):
    st = _ensure_student(db, student_id, body.grade_band or "6-8")
    if body.grade_band:
        st.grade_band = body.grade_band
    if body.hints_increment and body.topic_slug:
        tp = db.query(TopicProgress).filter_by(student_id=student_id, topic_slug=body.topic_slug).first()
        if tp:
            tp.hints_requested += body.hints_increment
        else:
            tp = TopicProgress(
                student_id=student_id,
                topic_slug=body.topic_slug,
                topic_title=body.topic_title or body.topic_slug,
                hints_requested=body.hints_increment,
            )
            db.add(tp)
    db.commit()
    db.refresh(st)
    return progress_get(student_id, db)
