import type { GradeBand } from "./student";

/** Empty in dev → same-origin requests use Vite proxy to the FastAPI server. */
const API_BASE = typeof import.meta.env.VITE_API_URL === "string" ? import.meta.env.VITE_API_URL : "";

async function j<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${API_BASE}${path}`, {
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

export type ChatRequestBody = {
  message: string;
  session_id: string;
  grade_level: GradeBand;
  lesson_context?: {
    topic?: string;
    section_title?: string;
    section_summary?: string;
  };
};

export async function postChat(body: ChatRequestBody): Promise<ChatRes> {
  return j("/chat", { method: "POST", body: JSON.stringify(body) });
}

/** Server-sent events: `content` chunks, then final `done` with metadata. */
export async function postChatStream(
  body: ChatRequestBody,
  onDelta: (chunk: string) => void
): Promise<{ hint_level: number; frustration_detected: boolean }> {
  const r = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || r.statusText);
  }
  const reader = r.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  let meta = { hint_level: 0, frustration_detected: false };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    for (;;) {
      const sep = buffer.indexOf("\n\n");
      if (sep === -1) break;
      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);

      for (const line of block.split("\n")) {
        if (!line.startsWith("data:")) continue;
        const raw = line.replace(/^data:\s?/, "").trim();
        if (!raw) continue;
        let data: {
          type?: string;
          content?: string;
          hint_level?: number;
          frustration_detected?: boolean;
        };
        try {
          data = JSON.parse(raw) as typeof data;
        } catch {
          continue;
        }
        if (data.type === "content" && data.content) onDelta(data.content);
        if (data.type === "done") {
          meta = {
            hint_level: data.hint_level ?? 0,
            frustration_detected: Boolean(data.frustration_detected),
          };
        }
      }
    }
  }

  return meta;
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
