import { getProgress, postProgressUpdate } from "@/lib/api";
import { getGradeBand, getStudentId, setGradeBand, type GradeBand } from "@/lib/student";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export function ProgressPage() {
  const sid = getStudentId();
  const [grade, setGrade] = useState<GradeBand>(getGradeBand());
  const [data, setData] = useState<Awaited<ReturnType<typeof getProgress>> | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getProgress(sid)
      .then(setData)
      .catch(() => setErr("Could not load progress. Is the API running?"));
  }, [sid]);

  async function syncGrade(g: GradeBand) {
    setGrade(g);
    setGradeBand(g);
    try {
      const p = await postProgressUpdate(sid, { grade_band: g });
      setData(p);
    } catch {
      /* ignore */
    }
  }

  return (
    <main id="main" className="mx-auto max-w-3xl px-4 py-10">
      <Link to="/" className="text-sageDark underline-offset-2 hover:underline">
        ← Home
      </Link>
      <h1 className="mt-6 font-display text-4xl font-bold text-ink">Your progress</h1>
      <p className="mt-2 text-lg text-slate-600">Topics, quizzes, and streaks — designed to celebrate effort.</p>

      {err && <p className="mt-6 rounded-lg bg-amber-50 px-4 py-3 text-amber-950">{err}</p>}

      <section className="mt-8 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15">
        <h2 className="font-display text-xl font-semibold text-ink">Grade band</h2>
        <div className="mt-4 flex flex-wrap gap-2">
          {(["K-5", "6-8", "9-12"] as const).map((g) => (
            <button
              key={g}
              type="button"
              onClick={() => void syncGrade(g)}
              className={`rounded-full px-4 py-2 text-lg font-medium ${
                grade === g ? "bg-sage text-white" : "bg-cream ring-1 ring-sage/20 hover:bg-sage/10"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </section>

      {data && (
        <>
          <section className="mt-6 rounded-2xl bg-sage/10 p-6 ring-1 ring-sage/20">
            <p className="text-sm font-medium uppercase tracking-wide text-sageDark">Learning streak</p>
            <p className="mt-2 font-display text-4xl font-bold text-ink">{data.current_streak} days</p>
            <p className="mt-2 text-slate-600">Show up to learn — small steps count.</p>
          </section>

          {data.incomplete_lesson_nudge && (
            <p className="mt-6 rounded-xl bg-peach/20 px-4 py-3 text-lg text-ink">{data.incomplete_lesson_nudge}</p>
          )}

          <section className="mt-8">
            <h2 className="font-display text-xl font-semibold text-ink">Topics this week</h2>
            {data.topics_this_week.length === 0 ? (
              <p className="mt-2 text-slate-600">Nothing logged yet — start a lesson from the dashboard.</p>
            ) : (
              <ul className="mt-4 list-inside list-disc text-lg text-slate-700">
                {data.topics_this_week.map((t) => (
                  <li key={t}>{t}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="mt-10">
            <h2 className="font-display text-xl font-semibold text-ink">By topic</h2>
            <div className="mt-4 space-y-4">
              {data.topics.length === 0 && <p className="text-slate-600">No topic rows yet.</p>}
              {data.topics.map((t) => (
                <div key={t.topic_slug} className="rounded-xl bg-white p-4 ring-1 ring-sage/15">
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <h3 className="font-semibold text-ink">{t.topic_title}</h3>
                    {t.lesson_incomplete && <span className="text-sm text-peach">Lesson in progress</span>}
                  </div>
                  <p className="mt-2 text-slate-600">
                    Lessons completed: {t.lessons_completed} · Hints in chat (tracked): {t.hints_requested}
                  </p>
                  <p className="mt-1 text-slate-600">
                    Latest quiz: {t.last_quiz_score != null ? `${t.last_quiz_score}%` : "—"}
                    {t.prev_quiz_score != null && t.last_quiz_score != null && (
                      <span className="ml-2">
                        (previous {t.prev_quiz_score}%)
                      </span>
                    )}
                  </p>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </main>
  );
}
