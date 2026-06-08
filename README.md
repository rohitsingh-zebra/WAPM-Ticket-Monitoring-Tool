# WAPM Ticket Monitoring Dashboard

Web dashboard for monitoring WAPM Jira tickets by `cluster_id`, `clientId Env`, `Alert Type`, and ticket.

Version 1 uses Jira as the source of truth and keeps all data in an in-memory FastAPI cache. No database is required.

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

- `docs/architecture.md`
- `docs/api.md`
- `docs/setup.md`
- `docs/deployment.md`
