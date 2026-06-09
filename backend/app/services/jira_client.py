from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import Settings
from app.models import Ticket


class JiraClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def fetch_recent_tickets(self, days: int = 7) -> list[Ticket]:
        jql_parts = [f'created >= -{days}d']
        if self.settings.jira_project_key:
            jql_parts.insert(0, f'project = "{self.settings.jira_project_key}"')

        fields = [
            "summary",
            "description",
            "status",
            "assignee",
            "created",
            "updated",
            "resolutiondate",
            "labels",
            "components",
            "issuetype",
            self.settings.jira_cluster_field,
            *self.settings.jira_client_env_field_ids,
        ]

        issues: list[dict[str, Any]] = []
        start_at = 0
        page_size = self.settings.jira_page_size

        async with httpx.AsyncClient(
            base_url=self.settings.jira_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.jira_pat}",
                "Accept": "application/json",
            },
            timeout=30.0,
        ) as client:
            while len(issues) < self.settings.jira_max_results:
                response = await client.get(
                    "/rest/api/2/search",
                    params={
                        "jql": " AND ".join(jql_parts) + " ORDER BY created DESC",
                        "startAt": start_at,
                        "maxResults": page_size,
                        "fields": ",".join(fields),
                    },
                )
                response.raise_for_status()
                payload = response.json()
                page = payload.get("issues", [])
                issues.extend(page)

                if start_at + len(page) >= payload.get("total", 0) or not page:
                    break
                start_at += len(page)

        return [self._to_ticket(issue) for issue in issues[: self.settings.jira_max_results]]

    def _to_ticket(self, issue: dict[str, Any]) -> Ticket:
        fields = issue.get("fields", {})
        created = self._parse_datetime(fields.get("created"))
        updated = self._parse_datetime(fields.get("updated"))
        resolution_date = self._parse_datetime(fields.get("resolutiondate"))

        return Ticket(
            id=str(issue.get("id", issue.get("key", ""))),
            key=str(issue.get("key", "")),
            summary=fields.get("summary") or "",
            description=self._extract_text(fields.get("description")),
            status=(fields.get("status") or {}).get("name", "Unknown"),
            assignee=self._extract_display_name(fields.get("assignee")),
            created=created,
            updated=updated,
            resolution_date=resolution_date,
            resolution_time_hours=self._resolution_hours(created, resolution_date),
            jira_url=f"{self.settings.jira_base_url}/browse/{issue.get('key', '')}",
            cluster=self._extract_field_value(fields.get(self.settings.jira_cluster_field)) or "Unassigned Cluster",
            organization=self._extract_client_env(fields) or "Unassigned Client Env",
            issue_type=(fields.get("issuetype") or {}).get("name") or "Unknown",
            labels=[str(label) for label in fields.get("labels") or []],
            components=[component.get("name", "") for component in fields.get("components") or []],
        )

    def _parse_datetime(self, value: str | None) -> datetime:
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    def _resolution_hours(self, created: datetime, resolution_date: datetime | None) -> float | None:
        if not resolution_date:
            return None
        return round((resolution_date - created).total_seconds() / 3600, 2)

    def _extract_display_name(self, value: dict[str, Any] | None) -> str | None:
        if not value:
            return None
        return value.get("displayName") or value.get("name") or value.get("emailAddress")

    def _extract_field_value(self, value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return ", ".join(filter(None, [self._extract_field_value(item) for item in value]))
        if isinstance(value, dict):
            return value.get("value") or value.get("name") or value.get("displayName")
        return str(value)

    def _extract_client_env(self, fields: dict[str, Any]) -> str | None:
        values = [
            self._extract_field_value(fields.get(field_id))
            for field_id in self.settings.jira_client_env_field_ids
        ]
        return " - ".join(value for value in values if value)

    def _extract_text(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return " ".join(self._extract_text(item) for item in value)
        if isinstance(value, dict):
            if "text" in value:
                return str(value["text"])
            return " ".join(self._extract_text(item) for item in value.values())
        return str(value)
