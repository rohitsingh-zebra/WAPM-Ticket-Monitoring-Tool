# API Documentation

Base URL: `http://localhost:8000`

## Health

`GET /health`

Returns backend health status.

## Dashboard Summary

`GET /api/dashboard/summary?days=2`

`GET /api/dashboard/summary?days=7`

Returns:

| Field | Description |
|-------|-------------|
| `total_tickets` | Total tickets in the selected date window |
| `open_tickets` | Tickets in Open / To Do status |
| `in_progress_tickets` | Tickets in In Progress status |
| `resolved_tickets` | Tickets in Resolved / Done / Closed status |
| `total_categories` | Number of distinct issue categories |
| `last_refresh_time` | UTC timestamp of the last successful cache refresh |

## Hierarchy

`GET /api/hierarchy?days=2`

`GET /api/hierarchy?days=7`

Returns a two-level tree:

```text
Issue Category -> Tickets
```

Each node is a `HierarchyNode`:

| Field | Description |
|-------|-------------|
| `id` | Unique node identifier |
| `label` | Display name (category name or ticket key + summary) |
| `type` | `"category"` or `"ticket"` |
| `count` | Ticket count for category nodes; `1` for ticket nodes |
| `children` | Child nodes (tickets under a category) |
| `ticket` | Full `Ticket` object when `type` is `"ticket"` |

## Ticket Model

Each cached ticket includes:

| Field | Description |
|-------|-------------|
| `key` | Jira ticket key (for example, `WAPM-11165`) |
| `summary` | Jira summary |
| `status` | Current Jira status |
| `category` | Dynamically derived issue category name |
| `cluster` | Jira `cluster_id` custom field value |
| `organization` | Jira client env custom field value(s) |
| `issue_type` | Jira issue type name (metadata only, not used for grouping) |
| `assignee` | Assignee display name |
| `created` / `updated` | Timestamps |
| `resolution_time_hours` | Hours from created to resolved, if resolved |
| `jira_url` | Direct link to the ticket in Jira |

## Ticket Details

`GET /api/tickets/{ticketId}`

Returns one cached ticket by Jira key.

## Search

`GET /api/search?q=keyword`

Searches cached tickets by:

- Ticket ID / key
- Issue category
- cluster_id
- clientId Env
- Summary

## Cache Status

`GET /api/cache/status`

Returns last refresh time, total cached ticket count, health status, and refresh error if present.

## Manual Refresh

`POST /api/cache/refresh`

Triggers an immediate Jira refresh. This is used by the dashboard refresh button.
