import { postChatStream, postLessonGenerateStream, postLessonNext, postProgressUpdate, resumeLesson, demoLessonGenerateStream, demoLessonNext, type LessonGenStreamEvent } from "@/lib/api";
import { ChatPanel, type ChatMessage } from "@/components/ChatPanel";
import { Markdown } from "@/components/Markdown";
import { getGradeBand, getStudentId, newSessionId, slugTopic, isDemoMode, type GradeBand } from "@/lib/student";
import { ArrowRight, ChevronLeft, Loader2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

type Section = Record<string, unknown>;

export function Learn() {
  const navigate = useNavigate();
  const location = useLocation();
  const state = location.state as { resumeSessionId?: string; grade?: string } | undefined;
  const studentId = useMemo(() => getStudentId(), []);
  const grade = useMemo(() => (state?.grade as GradeBand) || getGradeBand(), [state?.grade]);

  const [phase, setPhase] = useState<"centered" | "lesson">("centered");
  const [topic, setTopic] = useState("");
  const [lessonTitle, setLessonTitle] = useState("");
  const [outline, setOutline] = useState<string[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [sectionIndex, setSectionIndex] = useState(0);
  const [currentSection, setCurrentSection] = useState<Section | null>(null);
  const [loadingLesson, setLoadingLesson] = useState(false);
  const [generatingProgress, setGeneratingProgress] = useState<{ current: number; total: number } | null>(null);
  const [loadingNext, setLoadingNext] = useState(false);
  const [allSections, setAllSections] = useState<Section[]>([]);
  const [chatCollapsed, setChatCollapsed] = useState(false);

  const [chatSessionId, setChatSessionId] = useState(() => newSessionId());
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hi! I'm here to help you think — not to do the work for you. When you're ready, type what you want to learn below.",
    },
  ]);

  // Handle resume from past lessons
  useEffect(() => {
    if (state?.resumeSessionId) {
      (async () => {
        try {
          const res = await resumeLesson(state.resumeSessionId!);
          setSessionId(res.session_id);
          setLessonTitle(res.title);
          setOutline(res.outline);
          setSectionIndex(res.section_index);
          setCurrentSection(res.section);
          setPhase("lesson");
          setChatSessionId(newSessionId());
          setMessages([
            {
              role: "assistant",
              content: `Welcome back to **${res.title}**! You're on section ${res.section_index + 1} of ${res.total_sections}. Feel free to ask questions anytime!`,
            },
          ]);
        } catch (err) {
          console.error("Failed to resume lesson:", err);
        }
      })();
    }
  }, [state?.resumeSessionId]);

  async function handleStart(e: FormEvent) {
    e.preventDefault();
    const t = topic.trim();
    if (!t || loadingLesson) return;
    setLoadingLesson(true);
    setGeneratingProgress(null);
    const sid = newSessionId();
    setSessionId(sid);
    setChatSessionId(newSessionId());
    try {
      const onGeneratingEvent = (event: LessonGenStreamEvent) => {
        // Handle progress updates
        if (event.type === "progress" && event.current !== undefined && event.total !== undefined) {
          setGeneratingProgress({ current: event.current, total: event.total });
        } else if (event.type === "done") {
          setLessonTitle(event.title || "");
          setOutline(event.outline || []);
          setSectionIndex(event.section_index ?? 0);
          setCurrentSection(event.section || null);
          if (event.sections) {
            setAllSections(event.sections);
          }
          setPhase("lesson");
          setGeneratingProgress(null);
          setMessages([
            {
              role: "assistant",
              content: `We're starting **${event.title}**. Use this chat anytime you're stuck — I'll answer with questions and hints.`,
            },
          ]);
        } else if (event.type === "outline" && event.outline) {
          setOutline(event.outline);
        }
      };

      if (isDemoMode()) {
        await demoLessonGenerateStream({ topic: t, grade_level: grade, session_id: sid, student_id: studentId }, onGeneratingEvent);
      } else {
        await postLessonGenerateStream(
          {
            topic: t,
            grade_level: grade,
            session_id: sid,
            student_id: studentId,
          },
          onGeneratingEvent
        );
      }
    } catch (err) {
      setGeneratingProgress(null);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: `Could not start the lesson: ${String(err)}. Check that the API is running.` },
      ]);
    } finally {
      setLoadingLesson(false);
    }
  }

  async function handleNext() {
    if (!sessionId || loadingNext) return;
    setLoadingNext(true);
    try {
      const nextFn = isDemoMode() ? demoLessonNext : postLessonNext;
      const res = await nextFn({
        session_id: sessionId,
        completed_section_index: sectionIndex,
        student_id: studentId,
        ...(isDemoMode() && { topic }),
      });
      if (res.lesson_complete) {
        const enc = encodeURIComponent(topic.trim());
        navigate(`/quiz/${enc}`, { state: { topic: topic.trim(), grade } });
        return;
      }
      setSectionIndex(res.section_index);
      setCurrentSection(res.section);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", content: `Something went wrong: ${String(err)}` }]);
    } finally {
      setLoadingNext(false);
    }
  }

  function handlePrevious() {
    if (sectionIndex > 0) {
      setSectionIndex(sectionIndex - 1);
    }
  }

  function jumpToSection(index: number) {
    setSectionIndex(index);
    if (allSections && allSections[index]) {
      setCurrentSection(allSections[index]);
    }
  }

  async function handleChatSend(text: string) {
    setMessages((m) => [...m, { role: "user", content: text }, { role: "assistant", content: "" }]);
    const body = (currentSection?.body as string) || "";
    const summary = body.slice(0, 280);
    try {
      const res = await postChatStream(
        {
          message: text,
          session_id: chatSessionId,
          grade_level: grade,
          lesson_context: {
            topic: lessonTitle || topic,
            section_title: (currentSection?.title as string) || undefined,
            section_summary: summary || undefined,
          },
        },
        (chunk) => {
          setMessages((m) => {
            if (m.length === 0) return m;
            const next = [...m];
            const last = next[next.length - 1];
            if (last?.role !== "assistant") return m;
            next[next.length - 1] = { role: "assistant", content: last.content + chunk };
            return next;
          });
        }
      );
      if (res.frustration_detected) {
        try {
          await postProgressUpdate(studentId, {
            hints_increment: 1,
            topic_slug: slugTopic(topic || lessonTitle),
            topic_title: lessonTitle || topic,
          });
        } catch {
          /* offline */
        }
      }
    } catch (err) {
      setMessages((m) => {
        const next = [...m];
        const last = next[next.length - 1];
        if (last?.role === "assistant") {
          next[next.length - 1] = {
            role: "assistant",
            content: last.content || `Could not reach the tutor: ${String(err)}`,
          };
        }
        return next;
      });
    }
  }

  if (phase === "centered") {
    return (
      <main id="main" className="flex min-h-screen flex-col items-center justify-center px-4 py-12">
        <div className="w-full max-w-xl text-center">
          <Link to="/" className="mb-8 inline-block text-sageDark underline-offset-2 hover:underline">
            ← Home
          </Link>
          <h1 className="font-display text-3xl font-bold text-ink md:text-4xl">What would you like to learn today?</h1>
          <p className="mt-3 text-lg text-slate-600">Type a topic or question. We will build a short lesson — one section at a time.</p>
          <form onSubmit={handleStart} className="mt-10">
            <label htmlFor="topic" className="sr-only">
              Topic to learn
            </label>
            <textarea
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={3}
              placeholder="e.g. fractions, photosynthesis, the American Revolution…"
              className="w-full rounded-2xl border border-sage/25 bg-white px-4 py-4 text-xl text-ink shadow-sm placeholder:text-slate-400 focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/30"
            />
            <button
              type="submit"
              disabled={!topic.trim() || loadingLesson}
              className="mt-6 inline-flex items-center justify-center gap-2 rounded-full bg-sage px-8 py-4 text-lg font-semibold text-white shadow-md transition hover:bg-sageDark focus:outline-none focus:ring-2 focus:ring-sage disabled:opacity-50"
            >
              {loadingLesson ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Starting…
                </>
              ) : (
                <>
                  Begin
                  <ArrowRight className="h-5 w-5" aria-hidden />
                </>
              )}
            </button>
          </form>
          {generatingProgress && (
            <div className="mt-8 rounded-lg bg-sage/10 p-4">
              <p className="text-sm font-medium text-sageDark">
                Generating section {generatingProgress.current + 1} of {generatingProgress.total}...
              </p>
              <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-sage/20">
                <div
                  className="h-full bg-sage transition-all duration-300"
                  style={{
                    width: `${((generatingProgress.current + 1) / generatingProgress.total) * 100}%`,
                  }}
                />
              </div>
            </div>
          )}
        </div>
      </main>
    );
  }

  const bodyMd = (currentSection?.body as string) || "";
  const practice = (currentSection?.practice_prompt as string) || null;
  const secTitle = (currentSection?.title as string) || "Section";

  return (
    <main id="main" className="mx-auto flex min-h-screen max-w-7xl flex-col md:flex-row">
      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-6 md:px-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <Link to="/" className="text-sageDark underline-offset-2 hover:underline">
            ← Home
          </Link>
          <p className="text-sm text-slate-500">
            Section {sectionIndex + 1} of {Math.max(outline.length, sectionIndex + 1)}
          </p>
        </div>
        <article className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15 md:p-10" aria-labelledby="lesson-section-title">
          <h1 id="lesson-section-title" className="font-display text-3xl font-bold text-ink">
            {lessonTitle}
          </h1>
          <h2 className="mt-2 text-xl font-medium text-sageDark">{secTitle}</h2>
          <div className="prose-slate mt-6 max-w-none">
            <Markdown>{bodyMd}</Markdown>
          </div>
          {practice && (
            <div className="mt-8 rounded-xl bg-skySoft/80 p-5 ring-1 ring-sage/10">
              <p className="text-sm font-semibold uppercase tracking-wide text-sageDark">Try it</p>
              <p className="mt-2 text-lg text-ink">{practice}</p>
            </div>
          )}
          <div className="mt-10 flex flex-wrap gap-3">
            {sectionIndex > 0 && (
              <button
                type="button"
                onClick={handlePrevious}
                disabled={loadingNext}
                className="inline-flex items-center gap-2 rounded-full bg-slate-200 px-6 py-3 text-lg font-semibold text-ink shadow-sm transition hover:bg-slate-300 focus:outline-none focus:ring-2 focus:ring-slate-300 disabled:opacity-50"
              >
                <ChevronLeft className="h-5 w-5" aria-hidden />
                Previous
              </button>
            )}
            <button
              type="button"
              onClick={() => void handleNext()}
              disabled={loadingNext}
              className="inline-flex items-center gap-2 rounded-full bg-peach px-6 py-3 text-lg font-semibold text-ink shadow-sm transition hover:brightness-95 focus:outline-none focus:ring-2 focus:ring-peach disabled:opacity-50"
            >
              {loadingNext ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" aria-hidden />
                  Loading…
                </>
              ) : (
                <>
                  I'm done — what's next?
                  <ArrowRight className="h-5 w-5" aria-hidden />
                </>
              )}
            </button>
          </div>
        </article>

        {/* Section navigation bubbles */}
        {outline.length > 0 && (
          <div className="mt-8 rounded-2xl bg-white p-4 shadow-sm ring-1 ring-sage/15">
            <p className="mb-3 text-sm font-semibold text-slate-600">Jump to section:</p>
            <div className="flex flex-wrap gap-2">
              {outline.map((sectionName, idx) => (
                <button
                  key={idx}
                  onClick={() => jumpToSection(idx)}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                    idx === sectionIndex
                      ? "bg-sage text-white shadow-md ring-2 ring-sage"
                      : "bg-sage/10 text-sageDark hover:bg-sage/20 ring-1 ring-sage/20"
                  }`}
                  title={sectionName}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
      <div className="flex min-h-0 w-full flex-col md:w-[min(100%,380px)]">
        <ChatPanel
          title="Tutor chat"
          messages={messages}
          onSend={handleChatSend}
          collapsed={chatCollapsed}
          onToggleCollapse={() => setChatCollapsed((c) => !c)}
        />
      </div>
    </main>
  );
}
