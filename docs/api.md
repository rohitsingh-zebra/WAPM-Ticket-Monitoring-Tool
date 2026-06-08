# API Documentation

Base URL: `http://localhost:8000`

## Health

`GET /health`

Returns backend health status.

## Dashboard Summary

`GET /api/dashboard/summary?days=2`

`GET /api/dashboard/summary?days=7`

Returns total tickets, open tickets, in-progress tickets, resolved tickets, cluster count, client-env count, and last refresh time.

## Hierarchy

`GET /api/hierarchy?days=2`

`GET /api/hierarchy?days=7`

Returns:

```text
cluster_id -> clientId Env -> Alert Type -> Tickets
```

Each non-ticket node includes a ticket count.

## Ticket Details

`GET /api/tickets/{ticketId}`

Returns one cached ticket by Jira key.

## Search

`GET /api/search?q=keyword`

Searches cached tickets by:

- Ticket ID
- cluster_id
- clientId Env
- Alert Type
- Summary

## Cache Status

`GET /api/cache/status`

Returns last refresh time, total cached ticket count, health status, and refresh error if present.

## Manual Refresh

`POST /api/cache/refresh`

Triggers an immediate Jira refresh. This is used by the dashboard refresh button.
