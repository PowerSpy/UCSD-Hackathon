import { getPastLessons, resumeLesson } from "@/lib/api";
import { getGradeBand, getStudentId } from "@/lib/student";
import { Calendar, ChevronRight, Loader2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

type PastLesson = {
  session_id: string;
  topic: string;
  title: string;
  created_at: string | null;
  section_count: number;
  current_index: number;
  completed: boolean;
};

export function PastLessons() {
  const studentId = useMemo(() => getStudentId(), []);
  const grade = useMemo(() => getGradeBand(), []);
  const navigate = useNavigate();

  const [lessons, setLessons] = useState<PastLesson[]>([]);
  const [loading, setLoading] = useState(true);
  const [resuming, setResuming] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await getPastLessons(studentId);
        if (!cancelled) setLessons(res.lessons || []);
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to load past lessons:", err);
          setLessons([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [studentId]);

  async function handleResume(sessionId: string) {
    setResuming(sessionId);
    try {
      await resumeLesson(sessionId);
      navigate("/learn", { state: { resumeSessionId: sessionId, grade } });
    } catch (err) {
      console.error("Failed to resume lesson:", err);
      setResuming(null);
    }
  }

  const formatDate = (isoString: string | null) => {
    if (!isoString) return "Unknown date";
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return "Unknown date";
    }
  };

  if (loading) {
    return (
      <main id="main" className="flex min-h-screen items-center justify-center px-4">
        <Loader2 className="h-10 w-10 animate-spin text-sage" aria-hidden />
        <span className="sr-only">Loading past lessons</span>
      </main>
    );
  }

  return (
    <main id="main" className="mx-auto max-w-2xl px-4 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ink">Past Lessons</h1>
          <p className="mt-2 text-slate-600">Continue where you left off</p>
        </div>
        <Link to="/learn" className="text-sageDark underline-offset-2 hover:underline">
          ← Back to learn
        </Link>
      </div>

      {lessons.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-sage/30 px-6 py-12 text-center">
          <p className="text-lg text-slate-600">No past lessons yet. Start learning to see them here!</p>
          <Link to="/learn" className="mt-4 inline-block rounded-full bg-sage px-6 py-2 text-white hover:bg-sageDark">
            Start a new lesson
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {lessons.map((lesson) => (
            <div
              key={lesson.session_id}
              className="rounded-lg border border-sage/20 bg-white p-5 shadow-sm hover:shadow-md transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <h3 className="text-xl font-semibold text-ink truncate">{lesson.title}</h3>
                  <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-600">
                    <div className="flex items-center gap-1">
                      <Calendar className="h-4 w-4" aria-hidden />
                      {formatDate(lesson.created_at)}
                    </div>
                    <div>
                      Progress: {lesson.current_index + 1} of {lesson.section_count} sections
                    </div>
                    {lesson.completed && (
                      <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                        Completed
                      </span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleResume(lesson.session_id)}
                  disabled={resuming === lesson.session_id}
                  className="shrink-0 rounded-full bg-sage px-4 py-2 text-sm font-medium text-white transition hover:bg-sageDark disabled:opacity-50 inline-flex items-center gap-2 whitespace-nowrap"
                >
                  {resuming === lesson.session_id ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
                      Loading…
                    </>
                  ) : (
                    <>
                      Resume
                      <ChevronRight className="h-4 w-4" aria-hidden />
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
