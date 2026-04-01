import json
import logging
import re
import uuid
import asyncio
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from typing import Any

import httpx
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import llm
from app.chat_utils import (
    append_chat_history,
    hint_level_from_streak,
    lesson_context_text,
    update_frustration_streak,
)
from app.database import Base, engine, get_db
from app.grade_band import normalize_grade_band
from app.logging_conf import setup_logging
from app.models import Student, LessonSession, TopicProgress, LessonHistory, parse_json_list
from app.demo_data import DEMO_LESSONS, DEMO_QUIZZES
from app.schemas import (
    ChatRequest,
    ChatResponse,
    LessonGenerateRequest,
    LessonGenerateResponse,
    LessonNextRequest,
    LessonNextResponse,
    LessonHistoryResponse,
    PastLessonsResponse,
    ProgressGetResponse,
    ProgressTopic,
    ProgressUpdateBody,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizSubmitRequest,
    QuizSubmitResponse,
)

log = logging.getLogger(__name__)

# Ephemeral chat state: session_id -> { messages, failed_streak }
CHAT_STATE: dict[str, dict[str, Any]] = {}


def _ensure_tables():
    Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    _ensure_tables()
    log.info("API ready")
    yield


app = FastAPI(
    title="Socratic Learning Companion API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        log.warning("Health DB check failed: %s", e)
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return {"status": status, "database": db_ok}


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
async def chat_endpoint(body: ChatRequest):
    grade = normalize_grade_band(body.grade_level)
    sid = body.session_id
    state = CHAT_STATE.setdefault(sid, {"messages": [], "failed_streak": 0})

    update_frustration_streak(state, body.message)
    hint_level = hint_level_from_streak(state["failed_streak"])
    frustration = state["failed_streak"] >= 3

    lesson_context = lesson_context_text(body.lesson_context)

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
    except httpx.HTTPError as e:
        log.warning("Chat LLM request failed: %s", e)
        text = llm.offline_socratic_fallback(grade, hint_level)

    append_chat_history(state, body.message, text)

    return ChatResponse(
        response=text,
        lesson_generated=False,
        lesson_data=None,
        hint_level=hint_level,
        frustration_detected=frustration,
    )


def _sse_event(obj: dict[str, Any]) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"


@app.post("/chat/stream")
async def chat_stream_endpoint(body: ChatRequest):
    """SSE stream of assistant tokens; final event has type ``done`` and metadata."""
    grade = normalize_grade_band(body.grade_level)
    sid = body.session_id
    state = CHAT_STATE.setdefault(sid, {"messages": [], "failed_streak": 0})

    update_frustration_streak(state, body.message)
    hint_level = hint_level_from_streak(state["failed_streak"])
    frustration = state["failed_streak"] >= 3

    lesson_context = lesson_context_text(body.lesson_context)

    history = state["messages"]

    async def event_gen():
        parts: list[str] = []
        async for piece in llm.socratic_reply_stream(
            grade_band=grade,
            user_message=body.message,
            lesson_context=lesson_context,
            hint_level=hint_level,
            history=history,
        ):
            parts.append(piece)
            yield _sse_event({"type": "content", "content": piece})
        text = "".join(parts)
        append_chat_history(state, body.message, text)
        yield _sse_event(
            {
                "type": "done",
                "hint_level": hint_level,
                "frustration_detected": frustration,
            }
        )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/lesson/generate", response_model=LessonGenerateResponse)
async def lesson_generate(body: LessonGenerateRequest, db: Session = Depends(get_db)):
    grade = normalize_grade_band(body.grade_level)
    student_id = body.student_id or "anonymous"
    _ensure_student(db, student_id, grade)

    # Generate the first section to get title and outline
    data = await llm.generate_first_lesson_section(body.topic.strip(), grade)

    title = data.get("title") or body.topic
    outline = data.get("outline") or ["Introduction", "Example", "Guided practice"]
    section = data.get("section") or {}
    if not isinstance(outline, list):
        outline = ["Introduction", "Example", "Guided practice"]

    session_id = body.session_id or str(uuid.uuid4())
    
    # Generate ALL sections at once for faster loading
    log.info(f"Generating all {len(outline)} sections for lesson: {body.topic}")
    all_sections = await llm.generate_all_lesson_sections(
        body.topic.strip(),
        grade,
        outline,
    )
    
    row = LessonSession(
        session_id=session_id,
        student_id=student_id,
        topic=body.topic.strip(),
        grade_band=grade,
        outline_json=json.dumps(outline),
        sections_json=json.dumps(all_sections),
        current_index=0,
        completed=False,
        failed_attempts_chat=0,
    )
    db.merge(row)
    db.flush()

    # Save all sections to history
    try:
        for idx, section_data in enumerate(all_sections):
            section_history = LessonHistory(
                session_id=session_id,
                student_id=student_id,
                section_index=idx,
                section_name=section_data.get("title", outline[idx] if idx < len(outline) else f"Section {idx}"),
                subsection_name=section_data.get("subsection_name"),
                section_type=section_data.get("type", "intro"),
                content=section_data.get("body", ""),
                practice_prompt=section_data.get("practice_prompt"),
            )
            db.add(section_history)
        log.info(f"Added {len(all_sections)} sections to history: session={session_id}")
    except Exception as e:
        log.error(f"Failed to save section history: {e}")

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

    # Return the first section
    first_section = all_sections[0] if all_sections else section
    return LessonGenerateResponse(
        session_id=session_id,
        topic=body.topic.strip(),
        title=title,
        outline=outline,
        section=first_section,
        section_index=0,
        total_sections=len(outline),
    )


@app.post("/lesson/generate/stream")
async def lesson_generate_stream(body: LessonGenerateRequest, db: Session = Depends(get_db)):
    """Stream lesson generation with progress updates for each section being generated."""
    grade = normalize_grade_band(body.grade_level)
    student_id = body.student_id or "anonymous"
    _ensure_student(db, student_id, grade)

    # Generate the first section to get title and outline
    data = await llm.generate_first_lesson_section(body.topic.strip(), grade)

    title = data.get("title") or body.topic
    outline = data.get("outline") or ["Introduction", "Example", "Guided practice"]
    section = data.get("section") or {}
    if not isinstance(outline, list):
        outline = ["Introduction", "Example", "Guided practice"]

    session_id = body.session_id or str(uuid.uuid4())

    async def event_gen():
        # Emit outline at start
        yield _sse_event({"type": "outline", "outline": outline, "total": len(outline)})
        
        # Generate sections one by one, emitting progress
        all_sections = []
        for idx in range(len(outline)):
            if idx == 0:
                # Use already generated first section
                all_sections.append(section)
                yield _sse_event({
                    "type": "progress",
                    "current": idx,
                    "total": len(outline),
                    "section_name": outline[idx],
                })
            else:
                # Generate remaining sections
                yield _sse_event({
                    "type": "progress",
                    "current": idx,
                    "total": len(outline),
                    "section_name": outline[idx],
                })
                
                prior_summary = "\n".join(
                    f"- {s.get('title', 'section')}: {(s.get('body') or '')[:400]}" for s in all_sections
                )
                try:
                    section_data = await llm.generate_next_lesson_section(
                        body.topic.strip(),
                        grade,
                        outline,
                        prior_summary,
                        idx,
                    )
                    section_obj = section_data.get("section", {})
                    all_sections.append(section_obj)
                except Exception as e:
                    log.warning(f"Failed to generate section {idx}: {e}")
                    # Fallback section
                    section_obj = {
                        "type": "practice" if idx == len(outline) - 1 else "example",
                        "title": outline[idx] if idx < len(outline) else f"Section {idx}",
                        "subsection_name": outline[idx] if idx < len(outline) else "Continuation",
                        "body": f"Let's keep going with **{body.topic}**. What pattern do you notice from the last part?",
                        "practice_prompt": "Explain one idea from this lesson in your own words.",
                    }
                    all_sections.append(section_obj)

        # Save to database
        row = LessonSession(
            session_id=session_id,
            student_id=student_id,
            topic=body.topic.strip(),
            grade_band=grade,
            outline_json=json.dumps(outline),
            sections_json=json.dumps(all_sections),
            current_index=0,
            completed=False,
            failed_attempts_chat=0,
        )
        db.merge(row)
        db.flush()

        # Save all sections to history
        try:
            for idx, section_data in enumerate(all_sections):
                section_history = LessonHistory(
                    session_id=session_id,
                    student_id=student_id,
                    section_index=idx,
                    section_name=section_data.get("title", outline[idx] if idx < len(outline) else f"Section {idx}"),
                    subsection_name=section_data.get("subsection_name"),
                    section_type=section_data.get("type", "intro"),
                    content=section_data.get("body", ""),
                    practice_prompt=section_data.get("practice_prompt"),
                )
                db.add(section_history)
        except Exception as e:
            log.error(f"Failed to save section history: {e}")

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

        # Emit completion event with full response
        first_section = all_sections[0] if all_sections else section
        yield _sse_event({
            "type": "done",
            "session_id": session_id,
            "topic": body.topic.strip(),
            "title": title,
            "outline": outline,
            "section": first_section,
            "sections": all_sections,
            "section_index": 0,
            "total_sections": len(outline),
        })

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/lesson/next", response_model=LessonNextResponse)
async def lesson_next(body: LessonNextRequest, db: Session = Depends(get_db)):
    row = db.query(LessonSession).filter_by(session_id=body.session_id).first()
    if not row:
        raise HTTPException(404, "Session not found")

    outline = json.loads(row.outline_json or "[]")
    sections = json.loads(row.sections_json or "[]")
    completed = body.completed_section_index
    if not outline:
        raise HTTPException(400, "Lesson has no outline")
    if completed < 0 or completed >= len(outline):
        raise HTTPException(
            400,
            f"completed_section_index must be in 0..{len(outline) - 1}, got {completed}",
        )

    idx = completed + 1
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

    # Retrieve the next section from pre-generated sections (already in memory from lesson_generate)
    new_section = sections[idx] if idx < len(sections) else {}
    is_last = idx >= len(outline) - 1
    
    row.current_index = idx
    row.completed = False
    db.commit()

    log.info(f"Retrieved section: session={body.session_id}, index={idx}")

    return LessonNextResponse(
        section=new_section,
        section_index=idx,
        total_sections=len(outline),
        lesson_complete=is_last,
    )


@app.post("/quiz/generate", response_model=QuizGenerateResponse)
async def quiz_generate(body: QuizGenerateRequest):
    grade = normalize_grade_band(body.grade_level)
    perf = body.prior_performance
    data = await llm.generate_quiz(
        body.topic.strip(),
        grade,
        perf,
    )
    questions = data.get("questions") or []
    explanations = data.get("explanations") or {}
    return QuizGenerateResponse(topic=body.topic.strip(), questions=questions, explanations=explanations)


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
    grade = normalize_grade_band(body.grade_level)
    student_id = body.student_id or "anonymous"
    st = _ensure_student(db, student_id, grade)
    _update_streak(db, st)

    questions = body.questions or []
    feedback: list[dict[str, Any]] = []
    correct_n = 0
    explanations = body.explanations or {}
    for q in questions:
        qid = str(q.get("id") or "")
        ans = body.answers.get(qid, "")
        ok, _default_tip = _score_question(q, ans)
        if ok:
            correct_n += 1
            tip = "Great job! That's correct."
        else:
            # Use pre-generated explanation if available, otherwise fall back to default
            tip = explanations.get(qid, _default_tip)
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
    st = _ensure_student(db, student_id, normalize_grade_band(body.grade_band))
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


@app.get("/lesson/history/{session_id}", response_model=LessonHistoryResponse)
def get_lesson_history(session_id: str, db: Session = Depends(get_db)):
    """Retrieve all sections and subsections for a lesson session."""
    row = db.query(LessonSession).filter_by(session_id=session_id).first()
    if not row:
        raise HTTPException(404, "Session not found")
    
    history_rows = db.query(LessonHistory).filter_by(session_id=session_id).order_by(
        LessonHistory.section_index
    ).all()
    
    sections = [
        {
            "section_index": h.section_index,
            "section_name": h.section_name,
            "subsection_name": h.subsection_name,
            "section_type": h.section_type,
            "content": h.content,
            "practice_prompt": h.practice_prompt,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history_rows
    ]
    
    return LessonHistoryResponse(
        session_id=session_id,
        topic=row.topic,
        student_id=row.student_id,
        sections=sections,
    )


@app.get("/lessons/past/{student_id}", response_model=PastLessonsResponse)
def get_past_lessons(student_id: str, db: Session = Depends(get_db)):
    """Retrieve all past lessons for a student."""
    lessons = db.query(LessonSession).filter_by(student_id=student_id).order_by(
        LessonSession.created_at.desc()
    ).all()
    
    past_lessons = []
    for row in lessons:
        outline = json.loads(row.outline_json or "[]")
        past_lessons.append({
            "session_id": row.session_id,
            "topic": row.topic,
            "title": row.topic,  # You can customize this if you store title separately
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "section_count": len(outline),
            "current_index": row.current_index,
            "completed": row.completed,
        })
    
    return PastLessonsResponse(student_id=student_id, lessons=past_lessons)


@app.get("/lesson/resume/{session_id}", response_model=LessonGenerateResponse)
def resume_lesson(session_id: str, db: Session = Depends(get_db)):
    """Resume a past lesson session."""
    row = db.query(LessonSession).filter_by(session_id=session_id).first()
    if not row:
        raise HTTPException(404, "Session not found")
    
    outline = json.loads(row.outline_json or "[]")
    sections = json.loads(row.sections_json or "[]")
    current_idx = row.current_index
    
    # Get the current section
    current_section = sections[current_idx] if current_idx < len(sections) else (sections[0] if sections else {})
    
    return LessonGenerateResponse(
        session_id=session_id,
        topic=row.topic,
        title=row.topic,
        outline=outline,
        section=current_section,
        section_index=current_idx,
        total_sections=len(outline),
    )


# ==================== DEMO ENDPOINTS (for low API credit scenarios) ====================

@app.post("/demo/lesson/generate", response_model=LessonGenerateResponse)
async def demo_lesson_generate(body: LessonGenerateRequest):
    """Demo endpoint: return pre-generated lesson data without calling LLM."""
    topic_slug = body.topic.strip().lower().replace(" ", "_")
    
    if topic_slug not in DEMO_LESSONS:
        raise HTTPException(
            404,
            f"Demo lesson '{body.topic}' not available. Try: {', '.join(DEMO_LESSONS.keys())}"
        )
    
    demo_data = DEMO_LESSONS[topic_slug]
    session_id = body.session_id or str(uuid.uuid4())
    
    return LessonGenerateResponse(
        session_id=session_id,
        topic=body.topic.strip(),
        title=demo_data["title"],
        outline=demo_data["outline"],
        section=demo_data["sections"][0],
        section_index=0,
        total_sections=len(demo_data["sections"]),
    )


@app.post("/demo/lesson/generate/stream")
async def demo_lesson_generate_stream(body: LessonGenerateRequest):
    """Demo endpoint: stream pre-generated lesson sections."""
    topic = body.topic.strip()
    grade_level = body.grade_level or "6-8"
    session_id = body.session_id or str(uuid.uuid4())
    
    topic_slug = topic.lower().replace(" ", "_")
    
    if topic_slug not in DEMO_LESSONS:
        raise HTTPException(
            404,
            f"Demo lesson '{topic}' not available. Try: {', '.join(DEMO_LESSONS.keys())}"
        )
    
    demo_data = DEMO_LESSONS[topic_slug]
    outline = demo_data["outline"]
    all_sections = demo_data["sections"]
    
    async def event_gen():
        # Emit outline
        yield _sse_event({"type": "outline", "outline": outline, "total": len(outline)})
        
        # Emit progress for each section
        for idx in range(len(outline)):
            yield _sse_event({
                "type": "progress",
                "current": idx,
                "total": len(outline),
                "section_name": outline[idx],
            })
            # Small delay to simulate generation
            await asyncio.sleep(0.1)
        
        # Emit completion
        yield _sse_event({
            "type": "done",
            "session_id": session_id,
            "topic": topic,
            "title": demo_data["title"],
            "outline": outline,
            "section": all_sections[0],
            "sections": all_sections,
            "section_index": 0,
            "total_sections": len(outline),
        })
    
    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/demo/lesson/next", response_model=LessonNextResponse)
async def demo_lesson_next(body: LessonNextRequest):
    """Demo endpoint: retrieve next pre-generated section."""
    topic_slug = body.session_id.lower().replace(" ", "_")
    
    # Try to find matching demo lesson (this is a simplified version)
    # In a real scenario, you'd store the topic with the session
    for slug, lesson_data in DEMO_LESSONS.items():
        demo_data = lesson_data
        break
    
    if "demo_data" not in locals():
        raise HTTPException(400, "Demo lesson data not found")
    
    sections = demo_data["sections"]
    completed = body.completed_section_index
    outline = demo_data["outline"]
    
    if completed < 0 or completed >= len(outline):
        raise HTTPException(
            400,
            f"completed_section_index must be in 0..{len(outline) - 1}, got {completed}",
        )
    
    idx = completed + 1
    if idx >= len(outline):
        return LessonNextResponse(
            section={"type": "done", "title": "Lesson complete", "body": "Great work!", "practice_prompt": None},
            section_index=len(outline) - 1,
            total_sections=len(outline),
            lesson_complete=True,
        )
    
    new_section = sections[idx] if idx < len(sections) else {}
    is_last = idx >= len(outline) - 1
    
    return LessonNextResponse(
        section=new_section,
        section_index=idx,
        total_sections=len(outline),
        lesson_complete=is_last,
    )


@app.post("/demo/quiz/generate", response_model=QuizGenerateResponse)
async def demo_quiz_generate(body: QuizGenerateRequest):
    """Demo endpoint: return pre-generated quiz without calling LLM."""
    topic_slug = body.topic.strip().lower().replace(" ", "_")
    
    if topic_slug not in DEMO_QUIZZES:
        raise HTTPException(
            404,
            f"Demo quiz for '{body.topic}' not available. Try: {', '.join(DEMO_QUIZZES.keys())}"
        )
    
    demo_quiz = DEMO_QUIZZES[topic_slug]
    
    return QuizGenerateResponse(
        topic=body.topic.strip(),
        questions=demo_quiz["questions"],
        explanations=demo_quiz["explanations"],
    )


@app.get("/demo/available")
async def demo_available():
    """List available demo lessons and quizzes."""
    lessons = list(DEMO_LESSONS.keys())
    quizzes = list(DEMO_QUIZZES.keys())
    return {
        "available_lessons": lessons,
        "available_quizzes": quizzes,
        "note": "Use /demo/* endpoints instead of /lesson/* and /quiz/* endpoints",
        "chat_endpoint": "Chat still uses /chat and /chat/stream (real API calls)",
    }

