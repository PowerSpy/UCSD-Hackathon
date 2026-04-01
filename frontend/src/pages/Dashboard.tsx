import { BookOpen, LineChart, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProgress } from "@/lib/api";
import { getGradeBand, getStudentId, setGradeBand, type GradeBand } from "@/lib/student";

export function Dashboard() {
  const [grade, setGrade] = useState<GradeBand>("6-8");
  const [streak, setStreak] = useState(0);
  const [weekTopics, setWeekTopics] = useState<string[]>([]);

  useEffect(() => {
    setGrade(getGradeBand());
    const sid = getStudentId();
    getProgress(sid)
      .then((p) => {
        setStreak(p.current_streak);
        setWeekTopics(p.topics_this_week || []);
      })
      .catch(() => {
        /* offline */
      });
  }, []);

  function onGradeChange(g: GradeBand) {
    setGrade(g);
    setGradeBand(g);
  }

  return (
    <main id="main" className="mx-auto max-w-3xl px-4 py-10 md:py-16">
      <header className="mb-10 text-center">
        <p className="mb-2 inline-flex items-center gap-2 rounded-full bg-sage/10 px-4 py-1 text-sm font-medium text-sageDark">
          <Sparkles className="h-4 w-4" aria-hidden />
          Socratic Learning Companion
        </p>
        <h1 className="font-display text-4xl font-bold tracking-tight text-ink md:text-5xl">Learn by thinking out loud</h1>
        <p className="mt-4 text-xl text-slate-600">A friendly tutor that asks questions and offers hints — never shortcuts.</p>
      </header>

      <section className="mb-10 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15" aria-labelledby="grade-heading">
        <h2 id="grade-heading" className="mb-3 font-display text-xl font-semibold text-ink">
          Your grade band
        </h2>
        <p className="mb-4 text-lg text-slate-600">We will match vocabulary and examples to how you learn best.</p>
        <div className="flex flex-wrap gap-3" role="radiogroup" aria-label="Grade band">
          {(["K-5", "6-8", "9-12"] as const).map((g) => (
            <button
              key={g}
              type="button"
              role="radio"
              aria-checked={grade === g}
              onClick={() => onGradeChange(g)}
              className={`rounded-full px-5 py-2 text-lg font-medium transition focus:outline-none focus:ring-2 focus:ring-sage ${
                grade === g ? "bg-sage text-white shadow" : "bg-cream text-ink ring-1 ring-sage/25 hover:bg-sage/10"
              }`}
            >
              {g === "K-5" ? "K–5" : g === "6-8" ? "6–8" : "9–12"}
            </button>
          ))}
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2">
        <Link
          to="/learn"
          className="group flex flex-col rounded-2xl bg-sage p-6 text-white shadow-md transition hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-sageDark focus:ring-offset-2"
        >
          <BookOpen className="mb-3 h-10 w-10 opacity-90" aria-hidden />
          <span className="font-display text-2xl font-semibold">Start learning</span>
          <span className="mt-2 text-lg text-white/90">Tell us what you want to explore — we will build a lesson together.</span>
          <span className="mt-4 text-sm font-medium underline-offset-2 group-hover:underline">Go to lesson →</span>
        </Link>

        <Link
          to="/lessons/past"
          className="group flex flex-col rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15 transition hover:ring-sage/40 focus:outline-none focus:ring-2 focus:ring-sage"
        >
          <BookOpen className="mb-3 h-10 w-10 text-sage" aria-hidden />
          <span className="font-display text-2xl font-semibold text-ink">Past lessons</span>
          <span className="mt-2 text-lg text-slate-600">Continue where you left off — pick up any lesson.</span>
          <span className="mt-4 text-sm font-medium text-sageDark underline-offset-2 group-hover:underline">View lessons →</span>
        </Link>

        <Link
          to="/progress"
          className="flex flex-col rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15 transition hover:ring-sage/40 focus:outline-none focus:ring-2 focus:ring-sage"
        >
          <LineChart className="mb-3 h-10 w-10 text-sage" aria-hidden />
          <span className="font-display text-2xl font-semibold text-ink">Your progress</span>
          <span className="mt-2 text-lg text-slate-600">
            Streak: <strong className="text-ink">{streak}</strong> day{streak === 1 ? "" : "s"}
          </span>
          {weekTopics.length > 0 && (
            <span className="mt-2 text-base text-slate-600">This week: {weekTopics.slice(0, 3).join(", ")}</span>
          )}
          <span className="mt-4 text-sm font-medium text-sageDark underline-offset-2 hover:underline">View details →</span>
        </Link>
      </div>

      <p className="mt-10 text-center text-base text-slate-500">No timers, no pressure — just curiosity.</p>
    </main>
  );
}
