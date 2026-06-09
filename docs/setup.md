# Local Setup

## Prerequisites

- Python 3.12+
- Node.js 20+
- Jira PAT approved by the organization
- Jira custom field IDs for `cluster_id` and `clientId Env`

## Backend

```powershell
cd backend
copy .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Update `backend\.env`:

```env
JIRA_BASE_URL=https://jira.zebra.com
JIRA_PAT=replace-with-your-valid-pat
JIRA_PROJECT_KEY=Workforce AppMonitoring
JIRA_CLUSTER_FIELD=customfield_20014
JIRA_CLIENT_ENV_FIELDS=customfield_20034,customfield_20032
```

## Frontend

```powershell
cd frontend
copy .env.example .env
npm install
npm run dev
```

The dashboard runs at `http://localhost:5173`.

## Issue Categories

Tickets are grouped automatically by issue name extracted from the Jira summary. No configuration file is required.

When a new ticket pattern appears in Jira, the next cache refresh creates a new category group if the extracted issue name differs from existing categories.

To adjust how categories are parsed, edit `backend/app/services/category_classifier.py`.

## Dashboard Usage

1. Select **Last 2 Days** or **Last 7 Days** from the date filter.
2. Browse tickets in the **Tickets by Issue Category** tree.
3. Click a ticket to open the slide-in details panel from the right.
4. Use **Search** to find tickets by key, category, cluster, client env, or summary text.
5. Click **Refresh** to trigger an immediate Jira cache reload.
