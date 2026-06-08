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

## Alert Type Rules

Edit `backend\alert_type_rules.json` to change Alert Type matching without modifying code.

Example:

```json
{
  "Payroll": ["payroll"],
  "Timesheet": ["timesheet", "time sheet"]
}
```

Tickets that do not match any rule are assigned to `Others`.
