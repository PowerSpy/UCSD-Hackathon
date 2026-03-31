import type { GradeBand } from "./student";

const base = () => import.meta.env.VITE_API_URL || "";

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  return r.json() as Promise<T>;
}

export type ChatRes = {
  response: string;
  lesson_generated: boolean;
  lesson_data: unknown;
  hint_level: number;
  frustration_detected: boolean;
};

export async function postChat(body: {
  message: string;
  session_id: string;
  grade_level: GradeBand;
  lesson_context?: {
    topic?: string;
    section_title?: string;
    section_summary?: string;
  };
}): Promise<ChatRes> {
  return j("/chat", { method: "POST", body: JSON.stringify(body) });
}

export type LessonGenRes = {
  session_id: string;
  topic: string;
  title: string;
  outline: string[];
  section: Record<string, unknown>;
  section_index: number;
  total_sections: number;
};

export async function postLessonGenerate(body: {
  topic: string;
  grade_level: GradeBand;
  session_id: string;
  student_id: string;
}): Promise<LessonGenRes> {
  return j("/lesson/generate", { method: "POST", body: JSON.stringify(body) });
}

export type LessonNextRes = {
  section: Record<string, unknown>;
  section_index: number;
  total_sections: number;
  lesson_complete: boolean;
};

export async function postLessonNext(body: {
  session_id: string;
  completed_section_index: number;
  student_id: string;
}): Promise<LessonNextRes> {
  return j("/lesson/next", { method: "POST", body: JSON.stringify(body) });
}

export type QuizGenRes = { topic: string; questions: Record<string, unknown>[] };

export async function postQuizGenerate(body: {
  topic: string;
  grade_level: GradeBand;
  session_id?: string;
  student_id: string;
  prior_performance?: string;
}): Promise<QuizGenRes> {
  return j("/quiz/generate", { method: "POST", body: JSON.stringify(body) });
}

export type QuizSubmitRes = {
  score_percent: number;
  correct: number;
  total: number;
  feedback: { question_id: string; correct: boolean; encouragement: string }[];
};

export async function postQuizSubmit(body: {
  topic: string;
  grade_level: GradeBand;
  student_id: string;
  answers: Record<string, string>;
  questions: Record<string, unknown>[];
}): Promise<QuizSubmitRes> {
  return j("/quiz/submit", { method: "POST", body: JSON.stringify(body) });
}

export type ProgressRes = {
  student_id: string;
  grade_band: string;
  current_streak: number;
  topics_this_week: string[];
  topics: {
    topic_slug: string;
    topic_title: string;
    lessons_completed: number;
    hints_requested: number;
    last_quiz_score: number | null;
    prev_quiz_score: number | null;
    lesson_incomplete: boolean;
  }[];
  incomplete_lesson_nudge: string | null;
};

export async function getProgress(studentId: string): Promise<ProgressRes> {
  return j(`/progress/${encodeURIComponent(studentId)}`);
}

export async function postProgressUpdate(
  studentId: string,
  body: { grade_band?: GradeBand; hints_increment?: number; topic_slug?: string; topic_title?: string }
): Promise<ProgressRes> {
  return j(`/progress/${encodeURIComponent(studentId)}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
