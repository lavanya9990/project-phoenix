# Phoenix Project 4 - AI Workflow Automation

A full-stack lead qualification system. FastAPI persists enquiries, Groq returns validated structured analysis, n8n handles automation, and Next.js displays live results.

## Flow

Next.js form -> FastAPI -> SQLite -> Groq -> n8n webhook -> dashboard.

The lead is saved before external calls. Groq or n8n errors never delete it. Without a Groq key, deterministic local demo scoring is used. Without an n8n URL, workflow status is skipped.

## Setup

Backend (PowerShell):

    cd C:\Users\lavan\OneDrive\Desktop\Project-Phoenix\04-AI-Workflow-Automation\backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    Copy-Item .env.example .env
    uvicorn app.main:app --reload --port 8000

After copying the example, add your own Groq API key, your own n8n production
webhook URL, and a newly generated webhook secret to backend/.env. Never commit
backend/.env or paste its values into source code.

Frontend:

    cd C:\Users\lavan\OneDrive\Desktop\Project-Phoenix\04-AI-Workflow-Automation\frontend
    npm install
    Copy-Item .env.example .env.local
    npm run dev

Keep frontend/.env.local on your machine; it is intentionally gitignored.

n8n with Docker:

    docker volume create n8n_data
    docker run --name phoenix-n8n -p 5678:5678 -v n8n_data:/home/node/.n8n n8nio/n8n

Import n8n-workflows/lead-automation.json at localhost:5678, activate it, and copy its production webhook URL into backend/.env. It safely defaults to test mode and sends no email. Add Gmail or SMTP nodes after Prepare Email and Follow-up, select credentials inside n8n, and add a task provider node for production follow-ups. Never place credentials in workflow JSON.

## Security

- Secrets are loaded from environment variables.
- Local .env and .env.local files are gitignored.
- Gmail and SMTP credentials belong only in n8n's credential manager.
- Database files are local development artifacts and are not committed.
- Never place keys, credential IDs, private URLs, or passwords in workflow JSON.
- Rotate any key or webhook secret immediately if it is accidentally exposed.

## Scoring and API

Groq assesses need clarity, budget, timeline, urgency and purchase intent, returning JSON validated by Pydantic. Demo mode visibly scores enquiry detail, supplied budget and urgent timeline.

Endpoints: GET /health; POST/GET /api/leads; GET/PATCH/DELETE /api/leads/{id}; GET /api/dashboard/stats. Filters are lead_status, business_type, workflow_status and q. API docs are at localhost:8000/docs.

## Checks

    cd backend
    pytest
    cd ..\frontend
    npm run lint
    npm run build

## End-to-end test

Start all three services, import and activate the workflow, submit Add lead, inspect the qualification detail and n8n execution, then configure email credentials and repeat with a safe recipient.

## Limitations

This first version has no authentication, pagination, Alembic migrations, background queue or rate limiting. Real email and task actions require provider nodes and credentials in n8n. Production should add a job queue, migrations, secret verification inside the workflow, and an explicit duplicate-email policy.
