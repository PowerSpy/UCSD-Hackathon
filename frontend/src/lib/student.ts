const STUDENT_KEY = "slc_student_id";
const GRADE_KEY = "slc_grade_band";
const DEMO_MODE_KEY = "slc_demo_mode";

export type GradeBand = "K-5" | "6-8" | "9-12";

export function getStudentId(): string {
  try {
    let id = localStorage.getItem(STUDENT_KEY);
    if (!id) {
      id = crypto.randomUUID();
      localStorage.setItem(STUDENT_KEY, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

export function getGradeBand(): GradeBand {
  try {
    const g = localStorage.getItem(GRADE_KEY);
    if (g === "K-5" || g === "6-8" || g === "9-12") return g;
  } catch {
    /* ignore */
  }
  return "6-8";
}

export function setGradeBand(g: GradeBand): void {
  try {
    localStorage.setItem(GRADE_KEY, g);
  } catch {
    /* ignore */
  }
}

export function isDemoMode(): boolean {
  try {
    return localStorage.getItem(DEMO_MODE_KEY) === "true";
  } catch {
    return false;
  }
}

export function setDemoMode(enabled: boolean): void {
  try {
    localStorage.setItem(DEMO_MODE_KEY, enabled ? "true" : "false");
  } catch {
    /* ignore */
  }
}

export function newSessionId(): string {
  return crypto.randomUUID();
}

export function slugTopic(topic: string): string {
  return topic
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 200) || "topic";
}
