# Startup Guide

Use this guide to run the WAPM Ticket Monitoring Dashboard after cloning the repository.

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Access to Zebra Jira
- Valid Jira PAT

## 1. Clone And Open Project

```powershell
git clone https://github.com/rohitsingh-zebra/WAPM-Ticket-Monitoring-Tool.git
cd "WAPM-Ticket-Monitoring-Tool"
```

## 2. Backend Setup

Open a terminal in the project root and run:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Update `backend\.env`:

```env
JIRA_BASE_URL=https://jira.zebra.com
JIRA_PAT=<your-valid-jira-pat>
JIRA_PROJECT_KEY=Workforce AppMonitoring
JIRA_CLUSTER_FIELD=customfield_20014
JIRA_CLIENT_ENV_FIELDS=customfield_20034,customfield_20032
JIRA_PAGE_SIZE=100
JIRA_MAX_RESULTS=5000
CACHE_REFRESH_INTERVAL_MINUTES=5
ALERT_TYPE_RULES_FILE=alert_type_rules.json
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URL:

```text
http://127.0.0.1:8000
```

Useful checks:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/cache/status
http://127.0.0.1:8000/api/dashboard/summary?days=2
```

## 3. Frontend Setup

Open a second terminal in the project root and run:

```powershell
cd frontend
npm install
copy .env.example .env
```

Ensure `frontend\.env` contains:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Start the frontend:

```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend URL:

```text
http://127.0.0.1:5173/
```

## 4. Validate Jira Data

In Jira advanced search, validate the app's data with:

```jql
project = "Workforce AppMonitoring" AND created >= -2d ORDER BY created DESC
```

For the 7-day view:

```jql
project = "Workforce AppMonitoring" AND created >= -7d ORDER BY created DESC
```

## Notes

- The frontend never calls Jira directly. It calls the FastAPI backend only.
- The backend fetches Jira tickets into an in-memory cache.
- The cache refreshes every 5 minutes.
- Version 1 does not use a database.
- Do not commit a real `backend\.env` file or Jira PAT.
