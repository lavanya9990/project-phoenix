# Phoenix Project 3: AI Multi-Agent Research Assistant

A full-stack research workspace in which five LangGraph agents plan a topic, search the web, analyze evidence, check claims, and write a cited Markdown report. Research runs and failures are persisted in SQLite.

## Architecture

The FastAPI backend uses the shared `ResearchState` in `app/graph/state.py`. LangGraph executes `START -> planner -> researcher -> analyst -> fact_checker -> writer -> END`.

- **Planner:** creates 3, 5, or 8 validated research questions based on depth.
- **Researcher:** queries Tavily for every question, captures titles, URLs and snippets, and deduplicates URLs.
- **Analyst:** separates source-backed facts from interpretations and identifies patterns, risks, and opportunities.
- **Fact-checker:** labels claims supported, uncertain, or unsupported against the captured evidence.
- **Writer:** omits unsupported claims and returns a validated report. Application code appends the real source list to Markdown.

The Next.js dashboard provides research controls, workflow feedback, reports, source cards, copy/download actions, and persistent history with deletion.

## Setup

### Backend

```powershell
cd C:\Users\lavan\OneDrive\Desktop\Project-Phoenix\03-AI-Multi-Agent-Research-Assistant\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your `GROQ_API_KEY` and `TAVILY_API_KEY` to `backend/.env`. `GROQ_MODEL` is configurable; verify that the chosen model remains available on your Groq account.

Run:

```powershell
uvicorn app.main:app --reload --port 8000
```

API docs are available at `http://localhost:8000/docs`. A missing key, Tavily failure, or invalid LLM response produces a persisted failed result with an explanatory `error_message`.

### Frontend

In another terminal:

```powershell
cd C:\Users\lavan\OneDrive\Desktop\Project-Phoenix\03-AI-Multi-Agent-Research-Assistant\frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

## Test

```powershell
cd backend
pytest
curl http://localhost:8000/health
```

Then submit a topic in the UI. A live end-to-end run requires valid Groq and Tavily keys and consumes both services' quotas.

## API

- `GET /health`
- `POST /api/research`
- `GET /api/research`
- `GET /api/research/{research_id}`
- `DELETE /api/research/{research_id}`

## Current limitations

Research executes synchronously, so deep runs may take time and progress is currently staged client feedback rather than server-streamed node events. SQLite is intended for local single-instance use. Production deployment should use background jobs, streamed progress, authentication, rate limits, and a managed database.
