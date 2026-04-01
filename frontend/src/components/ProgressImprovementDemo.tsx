/**
 * Hard-coded demo chart for hackathon / judge walkthrough.
 * Shows quiz score improvement over attempts for two topics.
 */
const DEMO = {
  photosynthesis: {
    title: "Photosynthesis",
    scores: [58, 71, 84, 92],
    stroke: "#3D6B5C",
  },
  fractions: {
    title: "Fractions",
    scores: [50, 63, 76, 88],
    stroke: "#C97A4A",
  },
} as const;

const LABELS = ["Quiz 1", "Quiz 2", "Quiz 3", "Quiz 4"];

const W = 520;
const H = 240;
const PAD_L = 44;
const PAD_R = 20;
const PAD_T = 24;
const PAD_B = 40;

function seriesToPoints(scores: readonly number[]): string {
  const n = scores.length;
  if (n === 0) return "";
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  return scores
    .map((score, i) => {
      const x = PAD_L + (n === 1 ? innerW / 2 : (i / (n - 1)) * innerW);
      const y = PAD_T + innerH * (1 - Math.min(100, Math.max(0, score)) / 100);
      return `${x},${y}`;
    })
    .join(" ");
}

export function ProgressImprovementDemo() {
  const photoPts = seriesToPoints(DEMO.photosynthesis.scores);
  const fracPts = seriesToPoints(DEMO.fractions.scores);
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;
  const yTicks = [0, 25, 50, 75, 100];

  return (
    <section
      className="mt-8 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-sage/15"
      aria-labelledby="demo-improvement-heading"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="demo-improvement-heading" className="font-display text-xl font-semibold text-ink">
          Improvement over time
        </h2>
        <span className="rounded-full bg-skySoft px-3 py-1 text-xs font-semibold uppercase tracking-wide text-sageDark">
          Demo data
        </span>
      </div>
      <p className="mt-2 text-slate-600">
        Sample quiz scores across four attempts — illustrates growth for two topics (not tied to your account).
      </p>

      <figure className="mt-6">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="h-auto w-full max-w-full"
          role="img"
          aria-label="Line chart: Photosynthesis improves from 58 to 92 percent; Fractions from 50 to 88 percent over four quizzes."
        >
          <rect x={PAD_L} y={PAD_T} width={innerW} height={innerH} fill="#FDF8F3" rx={6} />

          {yTicks.map((pct) => {
            const y = PAD_T + innerH * (1 - pct / 100);
            return (
              <g key={pct}>
                <line
                  x1={PAD_L}
                  y1={y}
                  x2={PAD_L + innerW}
                  y2={y}
                  stroke="#E2E8F0"
                  strokeWidth={1}
                />
                <text x={PAD_L - 8} y={y + 4} textAnchor="end" className="fill-slate-500 text-[11px]">
                  {pct}%
                </text>
              </g>
            );
          })}

          {LABELS.map((label, i) => {
            const x = PAD_L + (LABELS.length === 1 ? innerW / 2 : (i / (LABELS.length - 1)) * innerW);
            return (
              <text
                key={label}
                x={x}
                y={H - 12}
                textAnchor="middle"
                className="fill-slate-600 text-[11px]"
              >
                {label}
              </text>
            );
          })}

          <polyline
            fill="none"
            stroke={DEMO.photosynthesis.stroke}
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            points={photoPts}
          />
          <polyline
            fill="none"
            stroke={DEMO.fractions.stroke}
            strokeWidth={2.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            points={fracPts}
          />

          {DEMO.photosynthesis.scores.map((score, i) => {
            const x = PAD_L + (LABELS.length === 1 ? innerW / 2 : (i / (LABELS.length - 1)) * innerW);
            const y = PAD_T + innerH * (1 - score / 100);
            return (
              <circle key={`p-${i}`} cx={x} cy={y} r={4} fill={DEMO.photosynthesis.stroke} />
            );
          })}
          {DEMO.fractions.scores.map((score, i) => {
            const x = PAD_L + (LABELS.length === 1 ? innerW / 2 : (i / (LABELS.length - 1)) * innerW);
            const y = PAD_T + innerH * (1 - score / 100);
            return (
              <circle key={`f-${i}`} cx={x} cy={y} r={4} fill={DEMO.fractions.stroke} />
            );
          })}
        </svg>
        <figcaption className="sr-only">
          Photosynthesis scores: {DEMO.photosynthesis.scores.join(", ")} percent. Fractions scores:{" "}
          {DEMO.fractions.scores.join(", ")} percent.
        </figcaption>
      </figure>

      <ul className="mt-4 flex flex-wrap gap-6 text-sm">
        <li className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: DEMO.photosynthesis.stroke }} />
          <span className="font-medium text-ink">{DEMO.photosynthesis.title}</span>
        </li>
        <li className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full" style={{ backgroundColor: DEMO.fractions.stroke }} />
          <span className="font-medium text-ink">{DEMO.fractions.title}</span>
        </li>
      </ul>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl bg-sage/10 p-4 ring-1 ring-sage/20">
          <h3 className="font-display text-lg font-semibold text-ink">{DEMO.photosynthesis.title}</h3>
          <p className="mt-1 text-3xl font-bold text-sageDark">
            Latest quiz: {DEMO.photosynthesis.scores[DEMO.photosynthesis.scores.length - 1]}%
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Started at {DEMO.photosynthesis.scores[0]}% · +{DEMO.photosynthesis.scores[DEMO.photosynthesis.scores.length - 1] - DEMO.photosynthesis.scores[0]} pts overall
          </p>
        </div>
        <div className="rounded-xl bg-peach/15 p-4 ring-1 ring-peach/30">
          <h3 className="font-display text-lg font-semibold text-ink">{DEMO.fractions.title}</h3>
          <p className="mt-1 text-3xl font-bold text-ink">
            Latest quiz: {DEMO.fractions.scores[DEMO.fractions.scores.length - 1]}%
          </p>
          <p className="mt-2 text-sm text-slate-600">
            Started at {DEMO.fractions.scores[0]}% · +{DEMO.fractions.scores[DEMO.fractions.scores.length - 1] - DEMO.fractions.scores[0]} pts overall
          </p>
        </div>
      </div>
    </section>
  );
}
