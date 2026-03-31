# Socratic Learning Companion

A full-stack K–12 learning app where an AI tutor **never gives direct answers** — it guides with questions, hints, and scaffolded reasoning. Built with **React (TypeScript) + Vite**, **FastAPI**, **SQLite**, and **OpenAI or Anthropic** APIs.

## Features

- **Centered “what do you want to learn?”** flow → structured lesson with sections revealed one at a time
- **Split layout** during lessons: lesson card + **collapsible Socratic chat**
- **Post-lesson quiz** (mixed question types) with encouraging feedback (no harsh timers)
- **Progress**: streaks, per-topic quiz history, incomplete-lesson nudges

## Architecture

```
frontend/     Vite + React + Tailwind + React Router
backend/      FastAPI + SQLAlchemy + SQLite
docs/         Socratic prompt rationale (see SOCRATIC_PROMPTS.md)
```

### API (FastAPI)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/chat` | Socratic reply; tracks frustration / hint level |
| `POST` | `/lesson/generate` | First lesson section + outline |
| `POST` | `/lesson/next` | Next section after student completes current |
| `POST` | `/quiz/generate` | Quiz JSON for a topic |
| `POST` | `/quiz/submit` | Score + store results |
| `GET` | `/progress/{student_id}` | Dashboard data |
| `POST` | `/progress/{student_id}` | Update grade band, hint counts |

The frontend uses a stable `student_id` from `localStorage` (UUID).

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Set OPENAI_API_KEY (or use Anthropic — see .env.example)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional: set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY` in `.env`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/chat`, `/lesson`, `/quiz`, and `/progress` to `http://127.0.0.1:8000` in development.

For production or custom API URL:

```bash
VITE_API_URL=https://your-api.example.com npm run build
```

Serve `frontend/dist` behind any static host; point `VITE_API_URL` at your FastAPI origin and enable CORS if needed (the API currently allows all origins for hackathon demos).

## Socratic design

See **[docs/SOCRATIC_PROMPTS.md](docs/SOCRATIC_PROMPTS.md)** and `backend/app/prompts.py` for the full rationale and prompt text. Judges care that the model is **constrained** to guiding behavior, with explicit rules against final answers and grade-level scaffolding.

## Demo / presentation

- Run backend + frontend locally, pick a topic, walk through one lesson section, ask the side chat a “give me the answer” question to show redirection, then complete the quiz.
- Record a short walkthrough if a public URL is not available.

## License

Hackathon / educational use — adapt as needed.
