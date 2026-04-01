import { postQuizGenerate, postQuizSubmit } from "@/lib/api";
import { getGradeBand, getStudentId, type GradeBand } from "@/lib/student";
import { CheckCircle2, Loader2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

type Q = Record<string, unknown>;

export function QuizPage() {
  const { topic: topicParam } = useParams();
  const location = useLocation();
  const state = location.state as { topic?: string; grade?: GradeBand } | undefined;
  const topic = state?.topic || decodeURIComponent(topicParam || "");
  const grade = useMemo(() => state?.grade || getGradeBand(), [state?.grade]);
  const studentId = useMemo(() => getStudentId(), []);

  const [questions, setQuestions] = useState<Q[]>([]);
  const [explanations, setExplanations] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<{ correct: boolean; encouragement: string } | null>(null);
  const [done, setDone] = useState(false);
  const [submitResult, setSubmitResult] = useState<{ score_percent: number; correct: number; total: number } | null>(null);

  useEffect(() => {
    if (!topic) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await postQuizGenerate({ topic, grade_level: grade, student_id: studentId });
        if (!cancelled) {
          setQuestions(res.questions || []);
          setExplanations(res.explanations || {});
        }
      } catch {
        if (!cancelled) setQuestions([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [topic, grade, studentId]);

  const q = questions[idx] as Q | undefined;
  const total = questions.length;
  const answeredCount = feedback ? idx + 1 : idx;
  const progress = total ? Math.round((answeredCount / total) * 100) : 0;

  function onAnswer(val: string) {
    if (!q) return;
    const id = String(q.id ?? idx);
    setAnswers((a) => ({ ...a, [id]: val }));
  }

  function checkCurrent() {
    if (!q) return;
    const id = String(q.id ?? idx);
    const ans = answers[id] || "";
    const type = q.type as string;
    const correct = String(q.correct || "");
    let ok = false;
    if (type === "multiple_choice") {
      ok = ans.trim().toLowerCase() === correct.trim().toLowerCase();
    } else {
      ok = ans.trim().length > 0 && correct.toLowerCase().split(/\s+/).some((w) => w.length > 3 && ans.toLowerCase().includes(w));
    }
    const encouragement = ok 
      ? "Great job! That's correct."
      : (explanations[id] || "That's okay — use the lesson ideas and try another angle.");
    setFeedback({
      correct: ok,
      encouragement,
    });
  }

  async function nextOrFinish() {
    if (!feedback) return;
    if (idx < total - 1) {
      setIdx((i) => i + 1);
      setFeedback(null);
      return;
    }
    setDone(true);
    try {
      const res = await postQuizSubmit({
        topic,
        grade_level: grade,
        student_id: studentId,
        answers,
        questions,
        explanations,
      });
      setSubmitResult({ score_percent: res.score_percent, correct: res.correct, total: res.total });
    } catch {
      setSubmitResult({ score_percent: 0, correct: 0, total: total });
    }
  }

  function onSubmitQuestion(e: FormEvent) {
    e.preventDefault();
    if (feedback) {
      void nextOrFinish();
      return;
    }
    checkCurrent();
  }

  if (loading) {
    return (
      <main id="main" className="flex min-h-screen items-center justify-center px-4">
        <Loader2 className="h-10 w-10 animate-spin text-sage" aria-hidden />
        <span className="sr-only">Loading quiz</span>
      </main>
    );
  }

  if (!topic || total === 0) {
    return (
      <main id="main" className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-lg text-slate-600">No quiz topic found. Start from a lesson first.</p>
        <Link className="mt-6 inline-block text-sageDark underline" to="/learn">
          Go to learn
        </Link>
      </main>
    );
  }

  if (done && submitResult) {
    return (
      <main id="main" className="mx-auto max-w-lg px-4 py-16 text-center">
        <CheckCircle2 className="mx-auto h-14 w-14 text-sage" aria-hidden />
        <h1 className="mt-4 font-display text-3xl font-bold text-ink">Quiz complete</h1>
        <p className="mt-4 text-2xl text-slate-700">
          You got <strong>{submitResult.correct}</strong> out of <strong>{submitResult.total}</strong> — about{" "}
          <strong>{submitResult.score_percent}%</strong>.
        </p>
        <p className="mt-4 text-lg text-slate-600">Scores help you see growth — they are not a judgment of you.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-4">
          <Link to="/" className="rounded-full bg-sage px-6 py-3 font-medium text-white hover:bg-sageDark">
            Dashboard
          </Link>
          <Link to="/progress" className="rounded-full bg-white px-6 py-3 font-medium text-sageDark ring-1 ring-sage/30 hover:bg-cream">
            Progress
          </Link>
        </div>
      </main>
    );
  }

  const type = (q?.type as string) || "short_answer";
  const choices = (q?.choices as string[] | null) || null;

  return (
    <main id="main" className="mx-auto max-w-2xl px-4 py-10">
      <Link to="/" className="text-sageDark underline-offset-2 hover:underline">
        ← Home
      </Link>
      <h1 className="mt-6 font-display text-3xl font-bold text-ink">Quiz: {topic}</h1>
      <p className="mt-2 text-lg text-slate-600">One question at a time. No timer — take the space you need.</p>

      <div className="mt-8" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-3 overflow-hidden rounded-full bg-sage/15">
          <div className="h-full rounded-full bg-sage transition-all" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-sm text-slate-500">
          Question {idx + 1} of {total}
        </p>
      </div>

      <form onSubmit={onSubmitQuestion} className="mt-10 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15 md:p-8">
        <p className="text-xl font-medium text-ink">{String(q?.prompt || "")}</p>

        {type === "multiple_choice" && choices && (
          <div className="mt-6 space-y-3" role="radiogroup">
            {choices.map((c) => {
              const id = String(q?.id ?? idx);
              const selected = answers[id] === c;
              return (
                <label
                  key={c}
                  className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 text-lg ${
                    selected ? "border-sage bg-sage/10" : "border-sage/20 hover:border-sage/40"
                  }`}
                >
                  <input
                    type="radio"
                    name={`q-${id}`}
                    checked={selected}
                    onChange={() => onAnswer(c)}
                    className="h-5 w-5 accent-sage"
                  />
                  {c}
                </label>
              );
            })}
          </div>
        )}

        {(type === "short_answer" || type === "fill_blank") && (
          <label className="mt-6 block">
            <span className="sr-only">Your answer</span>
            <textarea
              rows={4}
              value={answers[String(q?.id ?? idx)] || ""}
              onChange={(e) => onAnswer(e.target.value)}
              className="w-full rounded-xl border border-sage/25 px-4 py-3 text-lg focus:border-sage focus:outline-none focus:ring-2 focus:ring-sage/30"
              placeholder={type === "fill_blank" ? "Fill in the blank…" : "Type your answer…"}
            />
          </label>
        )}

        {feedback && (
          <div
            className={`mt-6 rounded-xl px-4 py-3 text-lg ${feedback.correct ? "bg-emerald-50 text-emerald-900" : "bg-amber-50 text-amber-950"}`}
            role="status"
          >
            {feedback.encouragement}
          </div>
        )}

        <div className="mt-8 flex gap-3">
          <button
            type="submit"
            className="rounded-full bg-sage px-6 py-3 font-semibold text-white hover:bg-sageDark focus:outline-none focus:ring-2 focus:ring-sage"
          >
            {feedback ? (idx < total - 1 ? "Next question" : "Finish") : "Check"}
          </button>
        </div>
      </form>
    </main>
  );
}
