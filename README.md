# WAPM Ticket Monitoring Dashboard

Web dashboard for monitoring WAPM Jira tickets grouped by **issue category** (derived dynamically from ticket summaries) with a slide-in ticket details panel.

Version 1 uses Jira as the source of truth and keeps all data in an in-memory FastAPI cache. No database is required.

## Features

- **Dynamic issue categories** — tickets are grouped by issue name extracted from the summary (for example, `Stuck UploadFile`, `Cognos Schdule Extracts files not found`). New categories appear automatically as new ticket patterns arrive.
- **Two-level hierarchy** — Issue Category → Tickets (no cluster or client-env nesting).
- **Slide-in details panel** — click a ticket to open an animated details drawer from the right; the ticket list shrinks to make room.
- **Search and filters** — search by ticket ID, issue category, cluster, client env, or summary; filter by last 2 or 7 days.
- **Summary metrics** — total, status breakdown, issue category count, and last refresh time.

## Stack

- Backend: FastAPI, Python 3.12+, APScheduler, httpx
- Frontend: React, Vite, Material UI, Axios, React Query
- Source: Jira REST API
- Storage: In-memory cache only

## Clone And Open Project

```powershell
git clone https://github.com/rohitsingh-zebra/WAPM-Ticket-Monitoring-Tool.git
cd "WAPM-Ticket-Monitoring-Tool"
```

## Quick Start

1. Configure backend environment:

```powershell
cd backend
copy .env.example .env
```

2. Edit `backend\.env` with the approved Jira PAT and the Jira custom field IDs for `cluster_id` and `clientId Env`.

3. Start the backend:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Start the frontend:

```powershell
cd ..\frontend
copy .env.example .env
npm install
npm run dev
```

5. Open `http://localhost:5173`.

## Documentation

- `startup.md` — step-by-step run guide
- `docs/architecture.md` — system design and data flow
- `docs/api.md` — REST API reference
- `docs/setup.md` — local development setup
