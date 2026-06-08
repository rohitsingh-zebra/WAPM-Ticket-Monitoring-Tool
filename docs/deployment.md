# Deployment Notes

## Backend

Run the FastAPI app with a production ASGI server:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Recommended production settings:

- Store Jira credentials in the platform secret manager.
- Set `CORS_ORIGINS` to the deployed frontend URL.
- Run one scheduler-owning backend instance unless scheduler coordination is added.
- Monitor `/health` and `/api/cache/status`.

## Frontend

Build static assets:

```powershell
npm run build
```

Serve the generated `frontend\dist` folder from the chosen internal web server.

Set:

```env
VITE_API_BASE_URL=https://wapm-dashboard-api.company.com
```

before building the frontend for production.

## Version 1 Constraints

- No user login.
- No database.
- No direct Jira calls from the browser.
- Cache is lost on backend restart and rebuilt from Jira on startup.
